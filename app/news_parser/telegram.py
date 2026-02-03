from datetime import timezone
from telethon import TelegramClient

from app.utils import normalize_text


async def parse_telegram_channel(
    client: TelegramClient,
    channel: str,
    source_name: str,
    content_type: str = "news",
) -> list[dict]:
    """
    Парсит сообщения из Telegram-канала и возвращает список новостей.

    Args:
        client: Авторизованный клиент Telegram для доступа к каналу.
        channel: Имя или ID Telegram-канала для парсинга.
        source_name: Название источника для идентификации новостей.
        content_type: Тип контента (по умолчанию "news").

    Returns:
        Список словарей с данными новостей, содержащих:
            - title: Заголовок (первая строка текста, до 200 символов)
            - url: URL новости (None для Telegram-сообщений)
            - summary: Краткое содержание (до 1500 символов)
            - source: Название источника
            - published_at: Дата и время публикации с UTC timezone
            - raw_text: Полный текст сообщения (до 4000 символов)
            - content_type: Тип контента

    Note:
        - Обрабатывает только последние 30 сообщений из канала
        - Пропускает сообщения без текста или с текстом короче 80 символов
        - Нормализует текст перед обработкой
    """
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