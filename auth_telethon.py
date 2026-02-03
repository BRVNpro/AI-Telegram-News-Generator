# python
"""
Модуль `auth_telethon` — создание и запуск сессии Telethon.

Этот модуль:
- загружает переменные окружения через `.env`,
- создаёт объект `TelegramClient` с параметрами из окружения:
  - `TG_SESSION_NAME` (имя сессии),
  - `TG_API_ID` (числовой API ID),
  - `TG_API_HASH` (API hash),
- стартует сессию и затем отключается.

Пример использования:
- импортировать функцию `create_telethon_client` и вызывать её в коде,
  либо запускать модуль напрямую: `python -m auth_telethon`.
"""
from telethon import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()


def create_telethon_client(session_name: str | None = None,
                           api_id: int | None = None,
                           api_hash: str | None = None) -> TelegramClient:
    """
    Создаёт и возвращает настроенный экземпляр `TelegramClient`.

    Аргументы (по умолчанию берутся из окружения):
        session_name (str | None): имя сессии (`TG_SESSION_NAME`).
        api_id (int | None): числовой API ID (`TG_API_ID`).
        api_hash (str | None): API hash (`TG_API_HASH`).

    Returns:
        TelegramClient: инициализированный клиент Telegram.

    Raises:
        ValueError: если необходимые переменные окружения отсутствуют или неверного типа.
    """
    session = session_name or os.getenv("TG_SESSION_NAME")
    raw_api_id = api_id if api_id is not None else os.getenv("TG_API_ID")
    hash_val = api_hash or os.getenv("TG_API_HASH")

    if session is None or raw_api_id is None or hash_val is None:
        raise ValueError("Missing one of TG_SESSION_NAME, TG_API_ID, TG_API_HASH in environment")

    try:
        api_id_int = int(raw_api_id)
    except (TypeError, ValueError):
        raise ValueError("TG_API_ID must be an integer")

    return TelegramClient(session, api_id_int, hash_val)


if __name__ == "__main__":
    client = create_telethon_client()
    client.start()
    print("✅ Telethon session created")
    client.disconnect()