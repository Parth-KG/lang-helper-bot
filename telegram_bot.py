import os
from telegram import Update
from dotenv import load_dotenv
from engine import process_text, transcribe_audio, synthesize_speech

from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a message and I'll reply.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    in_path = f"/tmp/{voice.file_id}.ogg"
    out_path = f"/tmp/{voice.file_id}_reply.mp3"

    try:
        await file.download_to_drive(in_path)

        text = transcribe_audio(in_path)
        result = process_text(text)

        synthesize_speech(result["output"], out_path)

        with open(out_path, "rb") as audio:
            await update.message.reply_voice(audio)
    finally:
        for path in (in_path, out_path):
            if os.path.exists(path):
                os.remove(path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    result = process_text(user_text)

    await update.message.reply_text(result["output"])

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.getenv("PORT", 8080)),
    url_path=TOKEN,
    webhook_url=f"{os.getenv('WEBHOOK_URL')}/{TOKEN}",
)