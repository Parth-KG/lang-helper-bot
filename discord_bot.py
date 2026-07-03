import os
import threading
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from engine import process_text

load_dotenv()
APP_ID = os.getenv("DISCORD_APP_ID")
PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")

if not all([APP_ID, PUBLIC_KEY]):
    raise SystemExit("Missing DISCORD_APP_ID or DISCORD_PUBLIC_KEY in your .env.")

verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
app = Flask(__name__)


def valid_signature(req):
    sig = req.headers.get("X-Signature-Ed25519", "")
    ts = req.headers.get("X-Signature-Timestamp", "")
    try:
        verify_key.verify(f"{ts}".encode() + req.data, bytes.fromhex(sig))
        return True
    except (BadSignatureError, ValueError):
        return False


def followup(token, text):
    url = f"https://discord.com/api/v10/webhooks/{APP_ID}/{token}/messages/@original"
    try:
        result = process_text(text)
        requests.patch(url, json={"content": result["output"]})
    except Exception as e:
        print(f"Error in followup: {e}")
        requests.patch(url, json={"content": "⚠️ Oops, I couldn't process that. Try again in a moment."})


@app.route("/discord", methods=["POST"])
def discord():
    if not valid_signature(request):
        return "invalid signature", 401

    data = request.json

    if data["type"] == 1:
        return jsonify({"type": 1})

    if data["type"] == 2 and data["data"]["name"] == "use":
        text = data["data"]["options"][0]["value"]
        token = data["token"]
        threading.Thread(target=followup, args=(token, text)).start()
        return jsonify({"type": 5})

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5002)))