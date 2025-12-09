import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from generar_pronosticos_multi_pdf import generar_pdf_multi_ligas

# Configuración de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy el Bot de SistGoy Apuestas.\n"
        "Usa /pdf para generar el reporte actualizado de pronósticos."
    )

async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"⏳ Generando reporte para ti, {user.first_name}... Esto puede tardar unos minutos.")

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

if __name__ == '__main__':
    # Obtener el token de las variables de entorno (seguridad)
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("Error: No se encontró la variable de entorno TELEGRAM_TOKEN")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pdf", generar_reporte))

    print("--- BOT INICIADO ---")
    app.run_polling()
