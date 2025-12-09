try:
    from fpdf import FPDF
except ImportError:
    from fpdf2 import FPDF
from fpdf.enums import XPos, YPos
import pronostico
from estadisticas_ligas import EstadisticasLiga
import datetime
from ligas_config import LIGAS
import unicodedata

def sanitize_text(text):
    if not isinstance(text, str):
        return str(text)
    # Normalize unicode characters to closest ASCII equivalent
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        # Title will be added in each page generation, keep header minimal

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 9)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Generado el {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                  new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

    def add_table_header(self, headers, col_widths):
        # Use larger, bold font for table headers
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(200, 220, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 10, sanitize_text(h), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
        self.ln()

    def add_table_row(self, row_data, col_widths, custom_fills=None):
        self.set_font('Helvetica', '', 6)
        for i, datum in enumerate(row_data):
            
            is_highlight = False
            fill_color = None
            text_color = (0, 0, 0)
            font_style = ''

            # 1. Custom Fill (Priority)
            if custom_fills and i in custom_fills:
                fill_color = custom_fills[i]
                is_highlight = True
                font_style = 'B'
            
            # 2. Percentage Logic
            elif isinstance(datum, str) and datum.endswith('%'):
                try:
                    val = float(datum.strip('%'))
                    if val > 75:
                        fill_color = (144, 238, 144) 
                        text_color = (0, 100, 0)      
                        font_style = 'B'
                        is_highlight = True
                except ValueError:
                    pass
            
            if is_highlight and fill_color:
                self.set_fill_color(*fill_color)
                self.set_text_color(*text_color)
                self.set_font('Helvetica', font_style, 6)
                fill = True
            else:
                self.set_fill_color(255, 255, 255)
                self.set_text_color(0, 0, 0)
                self.set_font('Helvetica', '', 6)
                fill = False

            self.cell(col_widths[i], 6, sanitize_text(str(datum)), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=fill)
        
        # Reset to default
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)
        self.ln()

def generar_pdf_multi_ligas():
    # Landscape orientation (L)
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    
    # Headers definition
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
        20, 8, 25, 10, 25, 10,       # Info with PPT added
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

    # List to store best match per league
    resumen_mejores = []
    
    for nombre_liga, url_liga in LIGAS.items():
        print(f"Procesando liga: {nombre_liga}...")
        
        try:
            # 1. Init Stats
            liga = EstadisticasLiga(url=url_liga)
            tabla = liga.tabla_posiciones()
            ppp_map = {row['Equipo']: row['PPP'] for row in tabla}
            
            # 2. Init Predictions
            pronosticador = pronostico.PronosticoPoisson(stats_liga=liga)
            todos = pronosticador.calcular_pronosticos_todos()
            pendientes = [p for p in todos if p["ResultadoReal"] == "N/A"]
            
            if not pendientes:
                print("   No hay partidos pendientes para esta liga.")
                continue

            # Filter by Date (Today + Tomorrow)
            hoy = datetime.date.today()
            manana = hoy + datetime.timedelta(days=1)
            print(f"   Fecha del sistema: {hoy}")
            print(f"   Partidos totales (pendientes): {len(pendientes)}")
            
            pendientes_filtrados = []
            for p in pendientes:
                fecha_partido = p.get('Fecha')
                if not fecha_partido:
                    continue
                
                fecha_obj = None
                if isinstance(fecha_partido, datetime.date):
                    fecha_obj = fecha_partido
                elif isinstance(fecha_partido, str):
                    # Attempt parse formats
                    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]:
                        try:
                            fecha_obj = datetime.datetime.strptime(fecha_partido, fmt).date()
                            break
                        except ValueError:
                            continue
                
                # Filter strictly for Today and Tomorrow
                if fecha_obj and (fecha_obj == hoy or fecha_obj == manana):
                    pendientes_filtrados.append(p)
            
            pendientes = pendientes_filtrados
            print(f"   Partidos para hoy ({hoy}) y mañana ({manana}): {len(pendientes)}")

            if not pendientes:
                # Do not print to PDF since we only want titles for active days
                continue

            # NOW we add the page - SKIPPED
            # pdf.add_page()
            # pdf.set_font('Helvetica', 'B', 14)
            # pdf.cell(0, 10, f'Liga: {sanitize_text(nombre_liga)}', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            # pdf.ln(5)

            # Sort by Date/Time
            pendientes.sort(key=lambda x: str(x.get('Fecha', '')))

            # --- Add top markets > 75% per match to Summary ---
            for p in pendientes:
                # Define all markets to check
                # (Label, Key in dict)
                markets_to_check = [
                    ("1", 'ProbLocal'), ("X", 'ProbEmpate'), ("2", 'ProbVisita'),
                    ("1X", 'Prob1X'), ("12", 'Prob12'), ("X2", 'ProbX2'),
                    ("BTTS Y", 'ProbAmbosMarcan'), ("BTTS N", 'ProbNoAmbosMarcan'),
                    (">0.5", 'ProbOver05'), ("<0.5", 'ProbUnder05'),
                    (">1.5", 'ProbOver15'), ("<1.5", 'ProbUnder15'),
                    (">2.5", 'ProbOver25'), ("<2.5", 'ProbUnder25'),
                    (">3.5", 'ProbOver35'), ("<3.5", 'ProbUnder35'),
                    (">4.5", 'ProbOver45'), ("<4.5", 'ProbUnder45'),
                    (">5.5", 'ProbOver55'), ("<5.5", 'ProbUnder55')
                ]

                # 1. Collect all valid probabilities > 75%
                match_options = []
                for label, key in markets_to_check:
                    try:
                        val = float(p.get(key, 0))
                        if val > 75:
                            match_options.append((label, val))
                    except (ValueError, TypeError):
                        continue
                
                # 2. Sort by probability descending
                match_options.sort(key=lambda x: x[1], reverse=True)

                # 3. Take ALL options > 75%
                all_options = match_options

                # 4. Add to summary if there are valid options
                # 4. Add to summary if there are valid options
                # 4. Add to summary if there are valid options
                # 4. Add to summary if there are valid options
                if all_options:
                    # Take top 7 options only to fit in columns
                    max_ops = 7
                    display_ops = all_options[:max_ops]
                    
                    # Create list of strings: "Pick (Prob%)" or "" if empty
                    ops_data = [f"{lbl} ({v:.0f}%)" for lbl, v in display_ops]
                    
                    # Pad with empty strings if fewer than max_ops
                    while len(ops_data) < max_ops:
                        ops_data.append("")
                    
                    resumen_mejores.append({
                        "Liga": nombre_liga,
                        "Fecha": str(p.get('Fecha', '')),
                        "Partido": f"{p['EquipoLocal']} vs {p['EquipoVisita']}",
                        "OpsList": ops_data,
                        "BestProb": all_options[0][1] # Use best prob for sorting
                    })

            # Table Header (Main League Page) - SKIPPED
            # pdf.add_table_header(headers, widths)

            for p in []: # SKIPPED DETAILED ROWS

                local = p['EquipoLocal']
                visita = p['EquipoVisita']
                
                ppp_local = ppp_map.get(local, 0.0)
                ppp_visita = ppp_map.get(visita, 0.0)
                
                row = [
                    str(p.get('Fecha', '')),
                    str(p['Jornada']),
                    local[:15], 
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
                ]
                
                # Custom Highlight
                custom_fills = {}
                if ppp_local > ppp_visita:
                    custom_fills[3] = (173, 216, 230) 
                elif ppp_visita > ppp_local:
                    custom_fills[5] = (173, 216, 230) 

                # Page break check
                if pdf.get_y() > 180:
                    pdf.add_page()
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.cell(0, 10, f'Liga: {sanitize_text(nombre_liga)} (Cont.)', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                    pdf.ln(5)
                    pdf.add_table_header(headers, widths)
                
                pdf.add_table_row(row, widths, custom_fills=custom_fills)

        except Exception as e:
            print(f"Error procesando {nombre_liga}: {e}")
            pdf.set_font('Helvetica', 'I', 10)
            pdf.cell(0, 10, f"Error al procesar datos: {sanitize_text(str(e))}", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # --- Generate Summary Page ---
    if resumen_mejores:
        # Sort: Date Ascending, Probability Descending
        def sort_key(item):
            # Parse Date
            f_str = item['Fecha']
            try:
                # Try standard format first
                d_obj = datetime.datetime.strptime(f_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    d_obj = datetime.datetime.strptime(f_str, "%d.%m.%Y").date()
                except ValueError:
                    d_obj = datetime.date.max # Push to end if parse fails
            
            # Use pre-calculated BestProb
            p_val = item['BestProb']
                
            return (d_obj, -p_val)

        resumen_mejores.sort(key=sort_key)

        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'Resumen: Apuestas de Alta Probabilidad (>75%) - Hoy y Mañana', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        
        # Table Headers: Multiple Columns for Options
        # Widths: Liga(35) + Date(20) + Match(50) = 105. Remaining = ~170?
        # 170 / 7 = ~24 per column.
        sum_headers = ["Liga", "Fecha", "Partido", "Op 1", "Op 2", "Op 3", "Op 4", "Op 5", "Op 6", "Op 7"]
        sum_widths = [35, 20, 50, 24, 24, 24, 24, 24, 24, 24]
        
        # Use a clearer, slightly larger font for summary headers
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(255, 215, 0) # Gold color for winners
        
        for i, h in enumerate(sum_headers):
            pdf.cell(sum_widths[i], 12, sanitize_text(h), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
        pdf.ln()
        
        # Slightly larger font for summary rows
        pdf.set_font('Helvetica', '', 8)
        for item in resumen_mejores:
            
            # Static row height is fine now since we are not multitasking vertical lists inside cells
            row_height = 8 
            
            pdf.cell(sum_widths[0], row_height, sanitize_text(item['Liga']), border=1)
            pdf.cell(sum_widths[1], row_height, sanitize_text(item['Fecha']), border=1)
            pdf.cell(sum_widths[2], row_height, sanitize_text(item['Partido'][:25]), border=1) # More truncation needed
            
            # Render Option Columns
            ops = item['OpsList']
            for i in range(7):
                txt = ops[i]
                if txt:
                    pdf.set_text_color(0, 100, 0) # Green
                    pdf.set_font('Helvetica', 'B', 7)
                    pdf.cell(sum_widths[3+i], row_height, sanitize_text(txt), border=1, align='C')
                else:
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(sum_widths[3+i], row_height, "-", border=1, align='C')
                    
            # Reset
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', '', 7)
            pdf.ln()

    output_filename = "Reporte_Multi_Ligas.pdf"
    pdf.output(output_filename)
    print(f"Reporte generado: {output_filename}")

if __name__ == "__main__":
    generar_pdf_multi_ligas()
