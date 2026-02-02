from datetime import timezone
from telethon import TelegramClient

from app.utils import normalize_text


async def parse_telegram_channel(
    client: TelegramClient,
    channel: str,
    source_name: str,
    content_type: str = "news",
) -> list[dict]:
    items: list[dict] = []

    async for msg in client.iter_messages(channel, limit=30):
        if not msg.message:
            continue

        text = normalize_text(msg.message)
        if len(text) < 80:
            continue

        title = text.split("\n", 1)[0][:200]
        dt = msg.date
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        items.append(
            {
                "title": title,
                "url": None,
                "summary": text[:1500],
                "source": source_name,
                "published_at": dt,
                "raw_text": text[:4000],
                "content_type": content_type,
            }
        )

    return items