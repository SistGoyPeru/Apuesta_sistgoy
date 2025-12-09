from fpdf import FPDF
from estadisticas_ligas import EstadisticasLiga
import pronostico
import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte de Análisis y Pronósticos de Liga', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Generado el {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, label, 0, 1, 'L', True)
        self.ln(4)

    def chapter_body_text(self, text):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, text)
        self.ln()

    def add_table(self, header, data, col_widths, align='C'):
        self.set_font('Arial', 'B', 9)
        # Header
        for i, h in enumerate(header):
            self.cell(col_widths[i], 7, h, 1, 0, 'C', True)
        self.ln()
        
        # Rows
        self.set_font('Arial', '', 8)
        for row in data:
            for i, datum in enumerate(row):
                self.cell(col_widths[i], 6, str(datum), 1, 0, align)
            self.ln()
        self.ln()

def generar_reporte():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Cargar Datos
    print("Calculando estadísticas...")
    liga = EstadisticasLiga()
    
    # 2. Resumen General
    pdf.chapter_title('Resumen General de la Temporada')
    
    resumen_txt = (
        f"Media de goles por partido: {liga.media_goles():.2f}\n"
        f"Total de partidos jugados: {liga.total_partidos_jugados()} / {liga.total_partidos_liga()}\n"
        f"Goles Local (Media): {liga.media_goles_local():.2f}\n"
        f"Goles Visita (Media): {liga.media_goles_visita():.2f}\n"
        f"Porcentaje Victorias Local: {liga.porcentaje_victorias_local():.2f}%\n"
        f"Porcentaje Empates: {liga.porcentaje_empates():.2f}%\n"
        f"Porcentaje Victorias Visita: {liga.porcentaje_victorias_visita():.2f}%\n"
        f"Ambos Marcan: {liga.porcentaje_ambos_marcan():.2f}%\n"
    )
    pdf.chapter_body_text(resumen_txt)

    # 3. Mercados de Goles (Over/Under)
    pdf.chapter_title('Estadísticas de Goles (Over/Under)')
    
    headers_ou = ["Mercado", "Porcentaje"]
    data_ou = [
        ["Over 0.5", f"{liga.porcentaje_over_05():.2f}%"],
        ["Over 1.5", f"{liga.porcentaje_over_15():.2f}%"],
        ["Over 2.5", f"{liga.porcentaje_over_25():.2f}%"],
        ["Over 3.5", f"{liga.porcentaje_over_35():.2f}%"],
        ["Under 2.5", f"{liga.porcentaje_under_25():.2f}%"],
        ["Under 3.5", f"{liga.porcentaje_under_35():.2f}%"],
    ]
    pdf.add_table(headers_ou, data_ou, [80, 40], align='L')

    # 4. Tabla de Posiciones
    pdf.add_page()
    pdf.chapter_title('Tabla de Posiciones')
    
    headers_table = ["Equipo", "Pts", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "PPP"]
    widths_table = [50, 10, 10, 10, 10, 10, 10, 10, 10, 15]
    
    data_table = []
    for row in liga.tabla_posiciones():
        data_table.append([
            row['Equipo'], row['Puntos'], row['PJ'], row['PG'], row['PE'], row['PP'],
            row['GF'], row['GC'], row['DG'], f"{row['PPP']:.2f}"
        ])
    
    pdf.add_table(headers_table, data_table, widths_table)

    # 5. Pronósticos
    pdf.add_page()
    pdf.chapter_title('Pronósticos Próxima Jornada (Modelo Poisson)')
    
    print("Calculando pronósticos...")
    pronosticador = pronostico.PronosticoPoisson()
    todos = pronosticador.calcular_pronosticos_todos()
    pendientes = [p for p in todos if p["ResultadoReal"] == "N/A"]
    
    if pendientes:
        # Definir columnas para la Tabla de Pronósticos
        # Jor, Local, Visita, 1, X, 2, +2.5, BTTS, Score
        
        headers_pred = ["Jor", "Local", "Visita", "1(%)", "X(%)", "2(%)", "+2.5(%)", "BTTS(%)", "Score"]
        widths_pred = [10, 40, 40, 12, 12, 12, 12, 12, 15]
        
        data_pred = []
        for p in pendientes: # Mostrar todos los pendientes
             data_pred.append([
                 str(p['Jornada']),
                 p['EquipoLocal'][:18],
                 p['EquipoVisita'][:18],
                 f"{p['ProbLocal']:.1f}",
                 f"{p['ProbEmpate']:.1f}",
                 f"{p['ProbVisita']:.1f}",
                 f"{p['ProbOver25']:.1f}",
                 f"{p['ProbAmbosMarcan']:.1f}",
                 p['MarcadorProbable']
             ])
        
        # Como pueden ser muchos, los paginamos o dejamos que fpdf maneje el salto de página
        pdf.add_table(headers_pred, data_pred, widths_pred)
    else:
        pdf.chapter_body_text("No hay partidos pendientes programados.")

    # Guardar Output
    output_filename = "Reporte_Liga_Pronosticos.pdf"
    pdf.output(output_filename)
    print(f"PDF generado exitosamente: {output_filename}")

if __name__ == "__main__":
    generar_reporte()
