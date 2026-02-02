from telethon import TelegramClient


async def publish_text(client: TelegramClient, target: str, text: str) -> None:
    await client.send_message(target, text)