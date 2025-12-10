from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, ApplicationBuilder, CommandHandler
import os
import logging
from generar_pronosticos_multi_pdf import generar_pdf_multi_ligas
import pronostico
from estadisticas_ligas import EstadisticasLiga
import datetime
from ligas_config import LIGAS

# Estados para el ConversationHandler avanzado
MENU, LIGA, EQUIPO, PARTIDO, TIPO_CONSULTA = range(5)
MENU, LIGA_ESTADISTICAS = range(2)

# Configuración de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- AQUÍ VAN TODAS LAS FUNCIONES DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    await update.message.reply_text(
        "👋 Bienvenido a SistGoy Apuestas ⚽️\n"
        "Aquí puedes consultar pronósticos, estadísticas y resultados de fútbol en tiempo real.\n"
        "Utiliza los comandos /pdf, /hoy, /apuesta o /menu para comenzar.\n"
        "¿Qué necesitas hoy?"
    )

async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    user = update.effective_user
    await update.message.reply_text(f"🔎🤖 Buscando y generando reporte para ti, {user.first_name}... Esto puede tardar unos minutos.")
    try:
        generar_pdf_multi_ligas()
        await update.message.reply_text("✅ Reporte generado. Subiendo archivo...")
        await update.message.reply_document(document=open("Reporte_Multi_Ligas.pdf", "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ Ocurrió un error: {str(e)}")

async def partidos_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_pronosticos = "\nPronósticos de la próxima jornada:\n"
    hoy = datetime.date.today()
    partidos_hoy = []
    mensaje = ""
    for nombre_liga, url_liga in LIGAS.items():
        estadisticas = EstadisticasLiga(url_liga)
        pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
        todos = pronostico_poisson.calcular_pronosticos_todos()
        pendientes = [p for p in todos if p.get('ResultadoReal', 'N/A') == 'N/A']
        if pendientes:
            mensaje_pronosticos += f"\nLiga: {nombre_liga}\n"
            for p in pendientes:
                mensaje_pronosticos += (
                    f"{p.get('EquipoLocal', p.get('Local', ''))} vs {p.get('EquipoVisita', p.get('Visita', ''))} | "
                    f"Marcador Probable: {p['MarcadorProbable']} | "
                    f"Local {p['ProbLocal']:.0f}%, Empate {p['ProbEmpate']:.0f}%, Visita {p['ProbVisita']:.0f}% | "
                    f"Over 2.5: {p.get('ProbOver25', 0):.0f}% | Ambos marcan: Sí {p.get('ProbAmbosMarcan', 0):.0f}%\n"
                )
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
                partidos_hoy.append(
                    f"Liga: {nombre_liga}\n"
                    f"Jornada: {p.get('Jornada', '')}\n"
                    f"Fecha: {fecha_obj.strftime('%d/%m/%Y')}\n"
                    f"Local: {p.get('EquipoLocal', p.get('Local', ''))}\n"
                    f"Visita: {p.get('EquipoVisita', p.get('Visita', ''))}\n"
                    f"Marcador Probable: {p['MarcadorProbable']}\n"
                    f"Probabilidades: Local {p['ProbLocal']:.0f}%, Empate {p['ProbEmpate']:.0f}%, Visita {p['ProbVisita']:.0f}%\n"
                    f"Doble oportunidad: 1X {p.get('Prob1X', 0):.0f}%, 12 {p.get('Prob12', 0):.0f}%, X2 {p.get('ProbX2', 0):.0f}%\n"
                    f"Over/Under: Over 0.5 {p.get('ProbOver05', 0):.0f}%, Under 0.5 {p.get('ProbUnder05', 0):.0f}% | Over 1.5 {p.get('ProbOver15', 0):.0f}%, Under 1.5 {p.get('ProbUnder15', 0):.0f}% | Over 2.5 {p.get('ProbOver25', 0):.0f}%, Under 2.5 {p.get('ProbUnder25', 0):.0f}%\n"
                    f"Ambos marcan: Sí {p.get('ProbAmbosMarcan', 0):.0f}%, No {p.get('ProbNoAmbosMarcan', 0):.0f}%\n"
                    f"Estado: {estado}\n"
                    "-----------------------------"
                )
    mensaje += mensaje_pronosticos
    await update.message.reply_text("🔎🤖 Buscando partidos de hoy, por favor espera...")
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    if partidos_hoy:
        mensaje += "\n".join(partidos_hoy)
    else:
        mensaje += "No hay partidos para hoy.\n"
    # Mostrar estadísticas de cada liga aunque no haya partidos
    for nombre_liga, url_liga in LIGAS.items():
        estadisticas = EstadisticasLiga(url_liga)
        total_jugados = estadisticas.total_partidos_jugados()
        total_liga = estadisticas.total_partidos_liga()
        goles_prom = estadisticas.media_goles()
        mensaje += f"\nEstadísticas de {nombre_liga}:\nPartidos jugados: {total_jugados}\nTotal partidos en liga: {total_liga}\nPromedio de goles por partido: {goles_prom:.2f}\n"
    await update.message.reply_text(mensaje)

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_TOKEN")
        exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pdf", generar_reporte))
    app.add_handler(CommandHandler("hoy", partidos_hoy))
    # Agrega aquí otros handlers si es necesario
    print("--- BOT INICIADO ---")
    app.run_polling()
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
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    await update.message.reply_text(
        "👋 Bienvenido a SistGoy Apuestas ⚽️\n"
        "Aquí puedes consultar pronósticos, estadísticas y resultados de fútbol en tiempo real.\n"
        "Utiliza los comandos /pdf, /hoy, /apuesta o /menu para comenzar.\n"
        "¿Qué necesitas hoy?"
    )

async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    user = update.effective_user
    await update.message.reply_text(f"🔎🤖 Buscando y generando reporte para ti, {user.first_name}... Esto puede tardar unos minutos.")

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
        mensaje_pronosticos = "\nPronósticos de la próxima jornada:\n"
        hoy = datetime.date.today()
        partidos_hoy = []
        mensaje = ""
        # Pronósticos de la próxima jornada
        for nombre_liga, url_liga in LIGAS.items():
            estadisticas = EstadisticasLiga(url_liga)
            pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
            todos = pronostico_poisson.calcular_pronosticos_todos()
            pendientes = [p for p in todos if p.get('ResultadoReal', 'N/A') == 'N/A']
            if pendientes:
                mensaje_pronosticos += f"\nLiga: {nombre_liga}\n"
                for p in pendientes:
                    mensaje_pronosticos += (
                        f"{p.get('EquipoLocal', p.get('Local', ''))} vs {p.get('EquipoVisita', p.get('Visita', ''))} | "
                        f"Marcador Probable: {p['MarcadorProbable']} | "
                        f"Local {p['ProbLocal']:.0f}%, Empate {p['ProbEmpate']:.0f}%, Visita {p['ProbVisita']:.0f}% | "
                        f"Over 2.5: {p.get('ProbOver25', 0):.0f}% | Ambos marcan: Sí {p.get('ProbAmbosMarcan', 0):.0f}%\n"
                    )
            # Partidos de hoy
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
                    partidos_hoy.append(
                        f"Liga: {nombre_liga}\n"
                        f"Jornada: {p.get('Jornada', '')}\n"
                        f"Fecha: {fecha_obj.strftime('%d/%m/%Y')}\n"
                        f"Local: {p.get('EquipoLocal', p.get('Local', ''))}\n"
                        f"Visita: {p.get('EquipoVisita', p.get('Visita', ''))}\n"
                        f"Marcador Probable: {p['MarcadorProbable']}\n"
                        f"Probabilidades: Local {p['ProbLocal']:.0f}%, Empate {p['ProbEmpate']:.0f}%, Visita {p['ProbVisita']:.0f}%\n"
                        f"Doble oportunidad: 1X {p.get('Prob1X', 0):.0f}%, 12 {p.get('Prob12', 0):.0f}%, X2 {p.get('ProbX2', 0):.0f}%\n"
                        f"Over/Under: Over 0.5 {p.get('ProbOver05', 0):.0f}%, Under 0.5 {p.get('ProbUnder05', 0):.0f}% | Over 1.5 {p.get('ProbOver15', 0):.0f}%, Under 1.5 {p.get('ProbUnder15', 0):.0f}% | Over 2.5 {p.get('ProbOver25', 0):.0f}%, Under 2.5 {p.get('ProbUnder25', 0):.0f}%\n"
                        f"Ambos marcan: Sí {p.get('ProbAmbosMarcan', 0):.0f}%, No {p.get('ProbNoAmbosMarcan', 0):.0f}%\n"
                        f"Estado: {estado}\n"
                        "-----------------------------"
                    )
        mensaje += mensaje_pronosticos
        await update.message.reply_text("🔎🤖 Buscando partidos de hoy, por favor espera...")
        try:
            with open("LOGO.JPG", "rb") as logo_file:
                await update.message.reply_photo(photo=logo_file)
        except Exception:
            pass
        if partidos_hoy:
            mensaje += "\n".join(partidos_hoy)
        else:
            mensaje += "No hay partidos para hoy.\n"
        # Mostrar estadísticas de cada liga aunque no haya partidos
        for nombre_liga, url_liga in LIGAS.items():
            estadisticas = EstadisticasLiga(url_liga)
