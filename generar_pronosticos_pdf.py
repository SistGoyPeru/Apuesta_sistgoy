from fpdf import FPDF
import pronostico
from estadisticas_ligas import EstadisticasLiga
import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Pronósticos Completos de la Liga (Modelo Poisson)', 0, 1, 'C')
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Generado el {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

    def add_table_header(self, headers, col_widths):
        self.set_font('Arial', 'B', 7)
        self.set_fill_color(200, 220, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, 1, 0, 'C', True)
        self.ln()

    def add_table_row(self, row_data, col_widths, custom_fills=None):
        self.set_font('Arial', '', 6)
        for i, datum in enumerate(row_data):
            
            is_highlight = False
            fill_color = None
            text_color = (0, 0, 0)
            font_style = ''

            # 1. Custom Fill (Priority)
            if custom_fills and i in custom_fills:
                fill_color = custom_fills[i] # Expect (r, g, b)
                is_highlight = True
                font_style = 'B' # Bold for custom highlights (PPT)
            
            # 2. Percentage Logic
            elif isinstance(datum, str) and datum.endswith('%'):
                try:
                    val = float(datum.strip('%'))
                    if val > 75:
                        fill_color = (144, 238, 144) # Light Green
                        text_color = (0, 100, 0)      # Dark Green
                        font_style = 'B'
                        is_highlight = True
                except ValueError:
                    pass
            
            if is_highlight and fill_color:
                self.set_fill_color(*fill_color)
                self.set_text_color(*text_color)
                self.set_font('Arial', font_style, 6)
                fill = True
            else:
                self.set_fill_color(255, 255, 255)
                self.set_text_color(0, 0, 0)
                self.set_font('Arial', '', 6)
                fill = False

            self.cell(col_widths[i], 6, str(datum), 1, 0, 'C', fill=fill)
        
        # Reset to default
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)
        self.ln()

def generar_pdf_pronosticos():
    # Landscape orientation (L)
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    
    print("Calculando estadísticas de posiciones (PPP)...")
    liga = EstadisticasLiga()
    tabla = liga.tabla_posiciones()
    # Crear mapa de Equipo -> PPP
    ppp_map = {row['Equipo']: row['PPP'] for row in tabla}

    print("Calculando pronósticos...")
    pronosticador = pronostico.PronosticoPoisson()
    todos = pronosticador.calcular_pronosticos_todos()
    pendientes = [p for p in todos if p["ResultadoReal"] == "N/A"]
    
    if not pendientes:
        print("No hay partidos pendientes.")
        return

    # Ordenar por Fecha
    pendientes.sort(key=lambda x: str(x.get('Fecha', '')))

    # Definir columnas
    # Basic: Fecha, Jor, Local, PPP L, Visita, PPP V
    
    headers = [
        "Fecha", "Jor", "Local", "PPT L", "Visita", "PPT V",
        "1", "X", "2", 
        "1X", "12", "X2",
        "BTTS Y", "BTTS N",
        "Score",
        ">0.5", "<0.5",
        ">1.5", "<1.5",
        ">2.5", "<2.5",
        ">3.5", "<3.5",
        ">4.5", "<4.5"
    ]
    
    widths = [
        20, 8, 25, 10, 25, 10,       # Info with PPT added, slight resize of names
        7, 7, 7,             # 1X2
        7, 7, 7,             # DC
        9, 9,                # BTTS
        10,                  # Score
        8, 8,                # 0.5
        8, 8,                # 1.5
        8, 8,                # 2.5
        8, 8,                # 3.5
        8, 8                 # 4.5
    ]
    headers.extend([">5.5", "<5.5"])
    widths.extend([8, 8])
    
    # Header
    pdf.add_table_header(headers, widths)
    
    for p in pendientes:
        local = p['EquipoLocal']
        visita = p['EquipoVisita']
        
        ppp_local = ppp_map.get(local, 0.0)
        ppp_visita = ppp_map.get(visita, 0.0)
        
        row = [
            str(p.get('Fecha', '')),
            str(p['Jornada']),
            local[:15], # Shorten slightly to fit column
            f"{ppp_local:.2f}",
            visita[:15],
            f"{ppp_visita:.2f}",
            f"{p['ProbLocal']:.0f}%", f"{p['ProbEmpate']:.0f}%", f"{p['ProbVisita']:.0f}%",
            f"{p['Prob1X']:.0f}%", f"{p['Prob12']:.0f}%", f"{p['ProbX2']:.0f}%",
            f"{p['ProbAmbosMarcan']:.0f}%", f"{p['ProbNoAmbosMarcan']:.0f}%",
            p['MarcadorProbable'],
            f"{p['ProbOver05']:.0f}%", f"{p['ProbUnder05']:.0f}%",
            f"{p['ProbOver15']:.0f}%", f"{p['ProbUnder15']:.0f}%",
            f"{p['ProbOver25']:.0f}%", f"{p['ProbUnder25']:.0f}%",
            f"{p['ProbOver35']:.0f}%", f"{p['ProbUnder35']:.0f}%",
            f"{p['ProbOver45']:.0f}%", f"{p['ProbUnder45']:.0f}%",
            f"{p['ProbOver55']:.0f}%", f"{p['ProbUnder55']:.0f}%",
        ]
        
        # Highlight higher PPP
        custom_fills = {}
        if ppp_local > ppp_visita:
            custom_fills[3] = (173, 216, 230) # Light Blue
        elif ppp_visita > ppp_local:
            custom_fills[5] = (173, 216, 230) # Light Blue

        # Check for page break
        if pdf.get_y() > 180: # A4 height is 210mm, leave footer space
            pdf.add_page()
            pdf.add_table_header(headers, widths)
            
        pdf.add_table_row(row, widths, custom_fills=custom_fills)

    output_filename = "Pronosticos_Todos_Encuentros.pdf"
    pdf.output(output_filename)
    print(f"PDF generado: {output_filename}")

if __name__ == "__main__":
    generar_pdf_pronosticos()
