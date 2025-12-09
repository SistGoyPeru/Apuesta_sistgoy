from estadisticas_ligas import EstadisticasLiga
from fpdf import FPDF

class GenerarPronosticoPDF:
    def __init__(self, nombre_archivo="pronostico_liga.pdf"):
        self.nombre_archivo = nombre_archivo

    def crear_pdf(self):
        liga = EstadisticasLiga()
        media = liga.media_goles()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt="Pronóstico de la Liga", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Media de goles por partido: {media:.2f}", ln=True, align="L")
        pdf.output(self.nombre_archivo)
        return self.nombre_archivo
