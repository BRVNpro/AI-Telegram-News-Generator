from telethon import TelegramClient


async def publish_text(client: TelegramClient, target: str, text: str) -> None:
    """
    Публикует текстовое сообщение в указанный Telegram чат или канал.

    Args:
        client: Экземпляр TelegramClient для отправки сообщений.
        target: Идентификатор целевого чата (username, ID или ссылка).
        text: Текст сообщения для публикации.

    Returns:
        None
    """
    await client.send_message(target, text)