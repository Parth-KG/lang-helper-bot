import os
import requests
from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("DISCORD_APP_ID")
TOKEN = os.getenv("DISCORD_TOKEN")

url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
command = {
    "name": "use",
    "description": "Fix your English or translate Hindi/Hinglish",
    "options": [
        {
            "name": "text",
            "description": "The text to correct or translate",
            "type": 3,          # string
            "required": True,
        }
    ],
}
resp = requests.post(url, headers={"Authorization": f"Bot {TOKEN}"}, json=command)
print(resp.status_code, resp.text)