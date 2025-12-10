import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from generar_pronosticos_multi_pdf import generar_pdf_multi_ligas
import pronostico
from estadisticas_ligas import EstadisticasLiga
import datetime
from ligas_config import LIGAS

# Configuración de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file, caption="\n\n", width=512)
    except Exception:
        pass
    await update.message.reply_text(
        "<b>🏟️🎲 ¡Bienvenido a SistGoy Apuestas! 🎲🏟️</b>\n\n"
        "<b>Tu casa de apuestas y estadísticas de fútbol 24/7</b> ⚽️🔥\n\n"
        "<b>Comandos rápidos:</b>\n"
        "• <b>/hoy</b> - Partidos y pronósticos del día\n"
        "• <b>/pdf</b> - Reporte PDF de pronósticos\n"
        "• <b>/start</b> - Menú principal\n\n"
        "<b>¿Qué te ofrecemos?</b>\n"
        "🎯 Pronósticos AI y estadísticas avanzadas\n"
        "📊 Over/Under, Doble oportunidad, Ambos marcan\n"
        "💸 ¡Aumenta tus chances y apuesta informado!\n"
        "📥 Descarga reportes y consulta resultados en tiempo real\n\n"
        "<i>¡Suerte y que ruede el balón! ⚽️💰</i>"
    , parse_mode='HTML')

async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    loading_msg = await update.message.reply_text("⚽️ Generando reporte, por favor espera...")

    try:
        # Ejecutar la lógica de generación
        # Nota: Esto es bloqueante. En producción idealmente se usaría un thread aparte,
        # pero para uso personal en Render/Railway está bien.
        generar_pdf_multi_ligas()
        
        # Enviar el archivo
        await update.message.reply_text("✅ Reporte generado. Subiendo archivo...")
        await update.message.reply_document(document=open("Reporte_Multi_Ligas.pdf", "rb"))

    except Exception as e:
        await update.message.reply_text(f"❌ Ocurrió un error: {str(e)}")

async def partidos_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loading_msg = await update.message.reply_text("⚽️ Buscando partidos de hoy, por favor espera...")
    hoy = datetime.date.today()
    partidos_hoy = []
    for nombre_liga, url_liga in LIGAS.items():
        estadisticas = EstadisticasLiga(url_liga)
        pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
        todos = pronostico_poisson.calcular_pronosticos_todos()
        for p in todos:
            fecha_partido = p.get('Fecha')
            fecha_obj = None
            if hasattr(fecha_partido, 'year') and hasattr(fecha_partido, 'month') and hasattr(fecha_partido, 'day'):
                fecha_obj = datetime.date(fecha_partido.year, fecha_partido.month, fecha_partido.day)
            else:
                for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]:
                    try:
                        fecha_obj = datetime.datetime.strptime(str(fecha_partido), fmt).date()
                        break
                    except Exception:
                        continue
            if fecha_obj == hoy:
                estado = "Pendiente" if p.get('ResultadoReal', 'N/A') == 'N/A' else f"Jugado ({p['ResultadoReal']})"
                hora = p.get('Hora', '')
                hora_str = f"Hora: {hora}\n" if hora else ""
                partidos_hoy.append(
                    f"Liga: {nombre_liga}\n"
                    f"Jornada: {p.get('Jornada', '')}\n"
                    f"Fecha: {fecha_obj.strftime('%d/%m/%Y')}\n"
                    f"{hora_str}"
                    f"Local: {p.get('EquipoLocal', p.get('Local', ''))}\n"
                    f"Visita: {p.get('EquipoVisita', p.get('Visita', ''))}\n"
                    f"Marcador Probable: {p['MarcadorProbable']}\n"
                    f"Probabilidades: Local {p['ProbLocal']:.0f}%, Empate {p['ProbEmpate']:.0f}%, Visita {p['ProbVisita']:.0f}%\n"
                    f"Doble oportunidad: 1X {p.get('Prob1X', 0):.0f}%, 12 {p.get('Prob12', 0):.0f}%, X2 {p.get('ProbX2', 0):.0f}%\n"
                    f"Over 0.5: {p.get('ProbOver05', 0):.0f}% | Over 1.5: {p.get('ProbOver15', 0):.0f}% | Over 2.5: {p.get('ProbOver25', 0):.0f}%\n"
                    f"Under 0.5: {p.get('ProbUnder05', 0):.0f}% | Under 1.5: {p.get('ProbUnder15', 0):.0f}% | Under 2.5: {p.get('ProbUnder25', 0):.0f}%\n"
                    f"Ambos marcan: Sí {p.get('ProbAmbosMarcan', 0):.0f}%, No {p.get('ProbNoAmbosMarcan', 0):.0f}%\n"
                    f"Estado: {estado}\n"
                    "-----------------------------"
                )
    if partidos_hoy:
        mensaje = "\n".join(partidos_hoy)
    else:
        mensaje = "No hay partidos para hoy."
    await update.message.reply_text(mensaje)

if __name__ == '__main__':
    # Obtener el token de las variables de entorno (seguridad)
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_TOKEN")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pdf", generar_reporte))
    app.add_handler(CommandHandler("hoy", partidos_hoy))

    print("--- BOT INICIADO ---")
    app.run_polling()
