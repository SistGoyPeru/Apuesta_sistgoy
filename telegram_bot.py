import matplotlib.pyplot as plt
import io
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from generar_pronosticos_multi_pdf import generar_pdf_multi_ligas
import pronostico
from estadisticas_ligas import EstadisticasLiga
import datetime
from ligas_config import LIGAS

async def menu_principal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if texto == "📅 Partidos de Hoy":
        await partidos_hoy(update, context)
    elif texto == "📊 Ligas y Estadísticas":
        await menu_ligas(update, context)
    elif texto == "📄 Reporte PDF":
        await generar_reporte(update, context)
    elif texto == "ℹ️ Ayuda":
        await update.message.reply_text(
            "<b>Ayuda SistGoy</b>\n\n"
            "• <b>Partidos de Hoy:</b> Muestra los partidos y pronósticos del día.\n"
            "• <b>Ligas y Estadísticas:</b> Consulta estadísticas y pronósticos de cada liga.\n"
            "• <b>Reporte PDF:</b> Descarga un reporte completo de pronósticos.\n"
            "• <b>Menú principal:</b> Vuelve a la portada.\n\n"
            "<i>Para cualquier consulta, escribe /start para volver al menú principal.</i>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("Por favor, selecciona una opción válida del menú.")
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from generar_pronosticos_multi_pdf import generar_pdf_multi_ligas
import pronostico
from estadisticas_ligas import EstadisticasLiga
import datetime
from ligas_config import LIGAS

# Estados para el menú de ligas
ESCOGIENDO_LIGA = 100

async def menu_ligas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ligas = list(LIGAS.keys())
    texto = "<b>Menú de Ligas Disponibles</b>\n\n"
    for idx, liga in enumerate(ligas, 1):
        texto += f"{idx}. {liga}\n"
    texto += "\nEscribe el número de la liga para ver sus estadísticas."
    await update.message.reply_text(texto, parse_mode='HTML')
    context.user_data['ligas_lista'] = ligas
    return ESCOGIENDO_LIGA

from telegram import ReplyKeyboardMarkup

ESCOGIENDO_PARTIDO = 101

async def mostrar_estadisticas_liga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ligas = context.user_data.get('ligas_lista', list(LIGAS.keys()))
    try:
        num = int(update.message.text.strip())
        if num < 1 or num > len(ligas):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Por favor, responde con el número de la liga.")
        return ESCOGIENDO_LIGA
    liga = ligas[num-1]
    url_liga = LIGAS[liga]
    estadisticas = EstadisticasLiga(url_liga)
    context.user_data['liga_seleccionada'] = liga
    context.user_data['estadisticas_liga'] = estadisticas
    # Mostrar próximos partidos como menú
    partidos = estadisticas.df.filter((estadisticas.df['GA'].is_null()) & (estadisticas.df['GV'].is_null()))
    if partidos.height == 0:
        await update.message.reply_text(
            "No hay partidos próximos para esta liga. Puedes volver al menú principal con /start.",
            reply_markup=ReplyKeyboardMarkup([["Menú principal"]], resize_keyboard=True)
        )
        return ConversationHandler.END
    texto = f"<b>Próximos encuentros de {liga}:</b>\n\n"
    keyboard = []
    lista_partidos = []
    for idx, row in enumerate(partidos.iter_rows(named=True), 1):
        local = row["Local"]
        visita = row["Visita"]
        jornada = row.get("Jornada", "")
        fecha = row.get("Fecha", "")
        texto += f"{idx}. {local} vs {visita} | Jornada: {jornada} | Fecha: {fecha}\n"
        keyboard.append([f"{idx}"])
        lista_partidos.append((local, visita, jornada, fecha))
    texto += "\nResponde con el número del partido para ver análisis y pronóstico."
    context.user_data['partidos_liga'] = lista_partidos
    await update.message.reply_text(texto, parse_mode='HTML', reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return ESCOGIENDO_PARTIDO

async def mostrar_analisis_partido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text.strip())
        partidos = context.user_data.get('partidos_liga', [])
        if num < 1 or num > len(partidos):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Por favor, responde con el número del partido.")
        return ESCOGIENDO_PARTIDO
    local, visita, jornada, fecha = context.user_data['partidos_liga'][num-1]
    liga = context.user_data.get('liga_seleccionada', '')
    estadisticas = context.user_data.get('estadisticas_liga')
    pronostico_poisson = pronostico.PronosticoPoisson(stats_liga=estadisticas)
    pred = pronostico_poisson.predecir_partido(local, visita)
    fuerza_local = pronostico_poisson.fuerzas.get(local, {})
    fuerza_visita = pronostico_poisson.fuerzas.get(visita, {})
    if not pred:
        await update.message.reply_text(
            "No hay datos suficientes para mostrar el pronóstico de este partido. Puedes intentar con otro partido o volver al menú principal con /start.",
            reply_markup=ReplyKeyboardMarkup([["Menú principal"]], resize_keyboard=True)
        )
        return ConversationHandler.END
    mensaje = (
        f"<b>{liga} - Jornada {jornada} ({fecha})</b>\n"
        f"<b>{local}</b> vs <b>{visita}</b>\n\n"
        f"<b>Pronóstico:</b>\n"
        f"Marcador probable: {pred['MarcadorProbable']}\n"
        f"Local: {pred['ProbLocal']:.1f}% | Empate: {pred['ProbEmpate']:.1f}% | Visita: {pred['ProbVisita']:.1f}%\n"
        f"Over 1.5: {pred['ProbOver15']:.1f}% | Over 2.5: {pred['ProbOver25']:.1f}%\n"
        f"Ambos marcan: Sí {pred['ProbAmbosMarcan']:.1f}% | No {pred['ProbNoAmbosMarcan']:.1f}%\n\n"
        f"<b>Estadísticas {local} (local):</b>\n"
        f"Ataque: {fuerza_local.get('local', {}).get('ataque', 0):.2f} | Defensa: {fuerza_local.get('local', {}).get('defensa', 0):.2f}\n"
        f"<b>Estadísticas {visita} (visita):</b>\n"
        f"Ataque: {fuerza_visita.get('visita', {}).get('ataque', 0):.2f} | Defensa: {fuerza_visita.get('visita', {}).get('defensa', 0):.2f}\n"
    )

    # Gráfico de barras comparativo
    try:
        fig, ax = plt.subplots(figsize=(6, 4))
        categorias = [f"{local}\nAtaque", f"{local}\nDefensa", f"{visita}\nAtaque", f"{visita}\nDefensa"]
        valores = [
            fuerza_local.get('local', {}).get('ataque', 0),
            fuerza_local.get('local', {}).get('defensa', 0),
            fuerza_visita.get('visita', {}).get('ataque', 0),
            fuerza_visita.get('visita', {}).get('defensa', 0)
        ]
        colores = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
        ax.bar(categorias, valores, color=colores)
        ax.set_ylabel('Fuerza')
        ax.set_title('Comparativa Ataque/Defensa')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        await update.message.reply_photo(photo=buf, caption="Comparativa visual de fuerzas de ataque y defensa")
    except Exception:
        await update.message.reply_text("No se pudo generar el gráfico. Puedes volver al menú principal con /start.")

    await update.message.reply_text(mensaje, parse_mode='HTML', reply_markup=ReplyKeyboardMarkup([["Menú principal"]], resize_keyboard=True))
    return ConversationHandler.END
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

    # Menú principal con botones
    keyboard = [
        [KeyboardButton("📅 Partidos de Hoy"), KeyboardButton("📊 Ligas y Estadísticas")],
        [KeyboardButton("📄 Reporte PDF"), KeyboardButton("ℹ️ Ayuda")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    bienvenida = (
        "<b>🏟️🎲 ¡Bienvenido a SistGoy Apuestas! 🎲🏟️</b>\n\n"
        "<b>Tu casa de apuestas y estadísticas de fútbol 24/7</b> ⚽️🔥\n\n"
        "<b>Menú principal:</b>\n"
        "Selecciona una opción con los botones de abajo 👇\n\n"
        "<b>¿Qué te ofrecemos?</b>\n"
        "🎯 Pronósticos AI y estadísticas avanzadas\n"
        "📊 Over/Under, Doble oportunidad, Ambos marcan\n"
        "💸 ¡Aumenta tus chances y apuesta informado!\n"
        "📥 Descarga reportes y consulta resultados en tiempo real\n\n"
        "<i>¡Suerte y que ruede el balón! ⚽️💰</i>"
    )
    await update.message.reply_text(bienvenida, parse_mode='HTML', reply_markup=reply_markup)

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
        # ConversationHandler para menú de ligas
    # Obtener el token de las variables de entorno (seguridad)
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_TOKEN")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pdf", generar_reporte))
    app.add_handler(CommandHandler("hoy", partidos_hoy))

    # ConversationHandler para menú de ligas (debe ir antes que el handler general de texto)
    conv_ligas = ConversationHandler(
        entry_points=[CommandHandler("ligas", menu_ligas)],
        states={
            ESCOGIENDO_LIGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, mostrar_estadisticas_liga)],
            ESCOGIENDO_PARTIDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, mostrar_analisis_partido)]
        },
        fallbacks=[CommandHandler("ligas", menu_ligas)]
    )
    app.add_handler(conv_ligas)

    # Handler para botones del menú principal (solo textos exactos de los botones)
    from telegram.ext import filters as tg_filters
    botones_principales = [
        "📅 Partidos de Hoy",
        "📊 Ligas y Estadísticas",
        "📄 Reporte PDF",
        "ℹ️ Ayuda",
        "Menú principal"
    ]
    filtro_botones = tg_filters.TEXT & tg_filters.Regex(f"^({'|'.join([b.replace(' ', '\\s') for b in botones_principales])})$")
    app.add_handler(MessageHandler(
        filtro_botones,
        menu_principal_handler
    ))

    print("--- BOT INICIADO ---")
    app.run_polling()
