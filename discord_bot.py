import os
import discord
from dotenv import load_dotenv
from engine import process_text

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        text = message.content.replace(f"<@{client.user.id}>", "").strip()
        if text:
            try:
                result = process_text(text)
                await message.channel.send(result["output"])
            except Exception as e:
                print(f"Error handling message: {e}")
                await message.channel.send("⚠️ Oops, I couldn't process that. Try again in a moment.")

if not TOKEN:
    raise SystemExit("DISCORD_TOKEN is missing. Add it to your .env file.")

client.run(TOKEN)