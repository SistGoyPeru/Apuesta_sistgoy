from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ContextTypes
# Estados para el ConversationHandler avanzado
MENU, LIGA, EQUIPO, PARTIDO, TIPO_CONSULTA = range(5)
def get_ligas_keyboard():
    ligas = list(LIGAS.keys())
    keyboard = [[KeyboardButton(liga)] for liga in ligas[:5]] # Solo las 5 primeras para no saturar
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
async def menu_avanzado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Enviar el logo primero
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
    await update.message.reply_text(
        "Bienvenido al bot avanzado de apuestas.\nElige una liga:",
        reply_markup=get_ligas_keyboard()
    )
    return LIGA
async def handle_liga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liga = update.message.text.strip()
    if liga not in LIGAS:
        await update.message.reply_text("Liga no encontrada. Elige una opción del teclado.", reply_markup=get_ligas_keyboard())
        return LIGA
    context.user_data['liga'] = liga
    await update.message.reply_text(
        f"Liga seleccionada: {liga}\n¿Quieres ver estadísticas, partidos, o pronósticos?",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("Estadísticas")],
            [KeyboardButton("Partidos")],
            [KeyboardButton("Pronósticos")]
        ], resize_keyboard=True)
    )
    return TIPO_CONSULTA
async def handle_tipo_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tipo = update.message.text.strip().lower()
    liga = context.user_data.get('liga')
    url_liga = LIGAS.get(liga)
    estadisticas = EstadisticasLiga(url_liga)
    if tipo == "estadísticas":
        total_jugados = estadisticas.total_partidos_jugados()
        total_liga = estadisticas.total_partidos_liga()
        goles_prom = estadisticas.media_goles()
        await update.message.reply_text(
            f"Estadísticas de {liga}:\nPartidos jugados: {total_jugados}\nTotal partidos: {total_liga}\nPromedio de goles: {goles_prom:.2f}"
        )
        return ConversationHandler.END
    elif tipo == "partidos":
        hoy = datetime.date.today()
        partidos = []
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
                partidos.append(f"{p.get('EquipoLocal', p.get('Local', ''))} vs {p.get('EquipoVisita', p.get('Visita', ''))} - {p['MarcadorProbable']} [{p.get('ResultadoReal', 'N/A')}]")
        if partidos:
            await update.message.reply_text("Partidos de hoy:\n" + "\n".join(partidos))
        else:
            await update.message.reply_text("No hay partidos para hoy en esta liga.")
        return ConversationHandler.END
    elif tipo == "pronósticos":
        pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
        todos = pronostico_poisson.calcular_pronosticos_todos()
        top_pronos = []
        for p in todos:
            top = max([
                (k, p.get(k, 0)) for k in ['ProbLocal','ProbEmpate','ProbVisita']
            ], key=lambda x: float(str(x[1]).replace('%','')))
            top_pronos.append(f"{p.get('EquipoLocal', p.get('Local', ''))} vs {p.get('EquipoVisita', p.get('Visita', ''))}: {top[0]} {float(str(top[1]).replace('%','')):.0f}%")
        if top_pronos:
            await update.message.reply_text("Top pronósticos:\n" + "\n".join(top_pronos))
        else:
            await update.message.reply_text("No hay pronósticos disponibles para esta liga.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Opción no reconocida. Elige una opción del teclado.")
        return TIPO_CONSULTA
from telegram.ext import MessageHandler, filters, ConversationHandler
# Estados para el ConversationHandler
MENU, LIGA_ESTADISTICAS = range(2)
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¿Qué información necesitas?\n"
        "1️⃣ Estadísticas de liga\n"
        "2️⃣ Resultados de hoy\n"
        "3️⃣ PDF de pronósticos\n"
        "Por favor, responde con el número o escribe el nombre de la liga para ver estadísticas."
    )
    return MENU
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "1" or "estadistica" in text.lower():
        ligas_disponibles = "\n".join([f"- {l}" for l in LIGAS.keys()])
        await update.message.reply_text(
            "¿De qué liga quieres ver estadísticas? Escribe el nombre exacto.\n"
            "Ligas disponibles:\n" + ligas_disponibles
        )
        return LIGA_ESTADISTICAS
    elif text == "2" or "resultados" in text.lower():
        await partidos_hoy(update, context)
        return ConversationHandler.END
    elif text == "3" or "pdf" in text.lower():
        await generar_reporte(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("No entendí tu respuesta. Por favor, responde con 1, 2, 3 o el nombre de la liga.")
        return MENU
async def handle_liga_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liga = update.message.text.strip()
    url_liga = LIGAS.get(liga)
    if not url_liga:
        ligas_disponibles = "\n".join([f"- {l}" for l in LIGAS.keys()])
        await update.message.reply_text(
            "No encontré esa liga. Por favor, escribe el nombre exacto.\n"
            "Ligas disponibles:\n" + ligas_disponibles
        )
        return LIGA_ESTADISTICAS
    estadisticas = EstadisticasLiga(url_liga)
    total_jugados = estadisticas.total_partidos_jugados()
    total_liga = estadisticas.total_partidos_liga()
    goles_prom = estadisticas.media_goles()
    await update.message.reply_text(
        f"Estadísticas de {liga}:\n"
        f"Partidos jugados: {total_jugados}\n"
        f"Total partidos en liga: {total_liga}\n"
        f"Promedio de goles por partido: {goles_prom:.2f}"
    )
    return ConversationHandler.END
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
    for nombre_liga, url_liga in LIGAS.items():
        estadisticas = EstadisticasLiga(url_liga)
        pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
        todos = pronostico_poisson.calcular_pronosticos_todos()
        # Buscar partidos pendientes (ResultadoReal == 'N/A')
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
    mensaje = mensaje_pronosticos
    await update.message.reply_text("🔎🤖 Buscando partidos de hoy, por favor espera...")
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file)
    except Exception:
        pass
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
    if partidos_hoy:
        mensaje += "\n" + "\n".join(partidos_hoy)
    else:
        mensaje += "\nNo hay partidos para hoy.\n"
    # Mostrar estadísticas de cada liga aunque no haya partidos
    for nombre_liga, url_liga in LIGAS.items():
        estadisticas = EstadisticasLiga(url_liga)
import os
import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ContextTypes

# Estados para el ConversationHandler avanzado
MENU, LIGA, EQUIPO, PARTIDO, TIPO_CONSULTA = range(5)
import os
import logging
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from generar_pronosticos_multi_pdf import generar_pdf_multi_ligas
import pronostico
from estadisticas_ligas import EstadisticasLiga
from ligas_config import LIGAS

# --- CONSTANTES PARA LOS ESTADOS DE CONVERSATIONHANDLER ---
MENU, LIGA_ESTADISTICAS, LIGA, TIPO_CONSULTA = range(4)

# --- HANDLERS PARA EL MENU Y CONVERSATION ---
async def menu_avanzado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menú avanzado (stub)")
    return LIGA

async def handle_liga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Liga seleccionada (stub)")
    return TIPO_CONSULTA

async def handle_tipo_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Consulta tipo (stub)")
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ligas = list(LIGAS.keys())
    opciones = ["Pronósticos", "Estadísticas", "Partidos Hoy", "PDF", "Salir"]
    filas = [ligas[i:i+3] for i in range(0, len(ligas), 3)]
    filas.append(opciones)
    teclado = ReplyKeyboardMarkup(filas, resize_keyboard=True)
    await update.message.reply_text(
        "Selecciona una liga o una opción:",
        reply_markup=teclado
    )
    return MENU

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Opción de menú (stub)")
    return LIGA_ESTADISTICAS

async def handle_liga_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Estadísticas de liga (stub)")
    return ConversationHandler.END

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mostrar logo en la portada principal
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file, width=800)
    except Exception:
        pass
        text = update.message.text.strip()
        if text == "1" or "estadistica" in text.lower():
            ligas_disponibles = "\n".join([f"- {l}" for l in LIGAS.keys()])
            await update.message.reply_text(
                "¿De qué liga quieres ver estadísticas? Escribe el nombre exacto.\n"
                "Ligas disponibles:\n" + ligas_disponibles
            )
            return LIGA_ESTADISTICAS
        elif text == "2" or "resultados" in text.lower():
            await partidos_hoy(update, context)

async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("LOGO.JPG", "rb") as logo_file:
            await update.message.reply_photo(photo=logo_file, width=800)
    except Exception:
        pass
        # ...existing code...
        pass

    async def partidos_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
        mensaje_pronosticos = "\nPronósticos de la próxima jornada:\n"
        for nombre_liga, url_liga in LIGAS.items():
            estadisticas = EstadisticasLiga(url_liga)
            pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
            todos = pronostico_poisson.calcular_pronosticos_todos()
            # Buscar partidos pendientes (ResultadoReal == 'N/A')
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
        mensaje += mensaje_pronosticos
        await update.message.reply_text("🔎🤖 Buscando partidos de hoy, por favor espera...")
        try:
            with open("LOGO.JPG", "rb") as logo_file:
                await update.message.reply_photo(photo=logo_file)
        except Exception:
            pass
        # ...existing code...
        partidos_hoy = []
        for p in partidos_hoy:
            estado = p.get('Estado', 'N/A')
            mensaje += (
                f"Visita: {p.get('EquipoVisita', p.get('Visita', ''))}\n"
                f"Marcador Probable: {p['MarcadorProbable']}\n"
                f"Probabilidades: Local {p['ProbLocal']:.0f}%, Empate {p['ProbEmpate']:.0f}%, Visita {p['ProbVisita']:.0f}%\n"
                f"Doble oportunidad: 1X {p.get('Prob1X', 0):.0f}%, 12 {p.get('Prob12', 0):.0f}%, X2 {p.get('ProbX2', 0):.0f}%\n"
                f"Over/Under: Over 0.5 {p.get('ProbOver05', 0):.0f}%, Under 0.5 {p.get('ProbUnder05', 0):.0f}% | Over 1.5 {p.get('ProbOver15', 0):.0f}%, Under 1.5 {p.get('ProbUnder15', 0):.0f}% | Over 2.5 {p.get('ProbOver25', 0):.0f}%, Under 2.5 {p.get('ProbUnder25', 0):.0f}%\n"
                f"Ambos marcan: Sí {p.get('ProbAmbosMarcan', 0):.0f}%, No {p.get('ProbNoAmbosMarcan', 0):.0f}%\n"
                f"Estado: {estado}\n"
                "-----------------------------"
            )
        if partidos_hoy:
            mensaje = "\n".join(partidos_hoy)
        else:
            mensaje = "No hay partidos para hoy.\n"
        # Mostrar estadísticas de cada liga aunque no haya partidos
        for nombre_liga, url_liga in LIGAS.items():
            estadisticas = EstadisticasLiga(url_liga)
        # ...existing code...

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
        # ConversationHandler avanzado con menú y botones
        conv_handler_adv = ConversationHandler(
            entry_points=[CommandHandler("apuesta", menu_avanzado)],
            states={
                LIGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_liga)],
                TIPO_CONSULTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tipo_consulta)],
            },
            fallbacks=[CommandHandler("apuesta", menu_avanzado)],
        )
        app.add_handler(conv_handler_adv)

        # ConversationHandler para menú interactivo
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", menu)],
            states={
                MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
                LIGA_ESTADISTICAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_liga_estadisticas)],
            },
            fallbacks=[CommandHandler("menu", menu)],
        )
    
        app.add_handler(conv_handler)

        app.run_polling()




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


# --- BLOQUE PRINCIPAL ---
import asyncio


async def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_TOKEN")
        exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pdf", generar_reporte))
    app.add_handler(CommandHandler("hoy", partidos_hoy))
    # ConversationHandler avanzado con menú y botones
    conv_handler_adv = ConversationHandler(
        entry_points=[CommandHandler("apuesta", menu_avanzado)],
        states={
            LIGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_liga)],
            TIPO_CONSULTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tipo_consulta)],
        },
        fallbacks=[CommandHandler("apuesta", menu_avanzado)],
    )
    app.add_handler(conv_handler_adv)

    # ConversationHandler para menú interactivo
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("menu", menu)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            LIGA_ESTADISTICAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_liga_estadisticas)],
        },
        fallbacks=[CommandHandler("menu", menu)],
    )
    app.add_handler(conv_handler)

    import asyncio
    async def main():
     await app.run_polling()

    try:
        try:
            loop = asyncio.get_running_loop()
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.ensure_future(main())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
    except ImportError:
        raise RuntimeError("nest_asyncio no está instalado. Instálalo con 'pip install nest_asyncio'")
    except Exception as e:
        print(f"Error ejecutando el bot: {e}")

if __name__ == "__main__":
    try:
        try:
            loop = asyncio.get_running_loop()
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.ensure_future(main())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
    except ImportError:
        raise RuntimeError("nest_asyncio no está instalado. Instálalo con 'pip install nest_asyncio'")
    except Exception as e:
        print(f"Error ejecutando el bot: {e}")
