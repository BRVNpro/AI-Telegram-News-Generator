from telethon import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TelegramClient(
    os.getenv("TG_SESSION_NAME"),
    int(os.getenv("TG_API_ID")),
    os.getenv("TG_API_HASH"),
)

client.start()
print("✅ Telethon session created")
client.disconnect()