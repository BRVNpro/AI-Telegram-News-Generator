from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
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