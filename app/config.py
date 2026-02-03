from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """
    Настройки приложения, загружаемые из переменных окружения.

    Attributes:
        database_url: URL для подключения к базе данных.
        redis_url: URL для подключения к Redis.
        celery_broker_url: URL брокера сообщений для Celery.
        celery_result_backend: URL бэкенда для хранения результатов Celery.
        ollama_base_url: Базовый URL для API Ollama.
        ollama_model: Название модели Ollama для использования.
        tg_api_id: ID приложения Telegram API.
        tg_api_hash: Hash приложения Telegram API.
        tg_session_name: Имя сессии для Telegram клиента.
        tg_target_channel: Целевой Telegram-канал для публикации.
        tg_source_channel: Исходный Telegram-канал для парсинга.
        rss_feed_url: URL RSS-ленты для парсинга новостей.
    """
    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    ollama_base_url: str
    ollama_model: str

    tg_api_id: int
    tg_api_hash: str
    tg_session_name: str

    tg_target_channel: str
    tg_source_channel: str

    rss_feed_url: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()