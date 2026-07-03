import os
import time
import uuid
import requests
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from engine import process_text, transcribe_audio, synthesize_speech

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL")

if not all([TWILIO_SID, TWILIO_TOKEN, PUBLIC_URL]):
    raise SystemExit("Missing Twilio env vars. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and PUBLIC_URL in your .env.")

AUDIO_DIR = "/tmp/wa_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

app = Flask(__name__)


def cleanup_old_audio(max_age_seconds=600):
    now = time.time()
    for f in os.listdir(AUDIO_DIR):
        path = os.path.join(AUDIO_DIR, f)
        if os.path.isfile(path) and now - os.path.getmtime(path) > max_age_seconds:
            os.remove(path)


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    cleanup_old_audio()

    resp = MessagingResponse()

    try:
        num_media = int(request.form.get("NumMedia", 0))
        media_type = request.form.get("MediaContentType0", "")
        is_voice = num_media > 0 and media_type.startswith("audio")

        if num_media > 0 and not is_voice:
            # an attachment that isn't audio (image, pdf, etc.)
            resp.message("I can only handle text and voice notes right now.")
            return str(resp)

        if is_voice:
            media_url = request.form.get("MediaUrl0")
            audio = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN))
            in_path = f"{AUDIO_DIR}/in_{uuid.uuid4().hex}.ogg"
            with open(in_path, "wb") as f:
                f.write(audio.content)
            incoming = transcribe_audio(in_path)
            os.remove(in_path)
        else:
            incoming = request.form.get("Body", "")

        result = process_text(incoming)

        if is_voice:
            fname = f"reply_{uuid.uuid4().hex}.mp3"
            out_path = f"{AUDIO_DIR}/{fname}"
            synthesize_speech(result["output"], out_path)
            resp.message().media(f"{PUBLIC_URL}/audio/{fname}")
        else:
            resp.message(result["output"])

    except Exception as e:
        print(f"Error handling WhatsApp message: {e}")
        resp.message("⚠️ Oops, I couldn't process that. Try again in a moment.")

    return str(resp)


@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    app.run(port=5001)