# python
"""
Модуль `app.main` — точка входа FastAPI-приложения.

Этот модуль:
- создаёт экземпляр FastAPI с метаданными (title, version);
- предоставляет lifespan, который инициализирует схему БД (вызов `Base.metadata.create_all`)
  при старте приложения;
- подключает маршруты API из `app.api.endpoints`.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db import engine, Base
from app.api.endpoints import router as api_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan контекстный менеджер для FastAPI.

    При старте приложения выполняет инициализацию схемы базы данных
    (создаёт все таблицы, описанные в `Base`). После инициализации
    управление передаётся приложению. При необходимости сюда можно добавить
    логику завершения работы (закрытие соединений, очистка ресурсов и т.д.).

    Args:
        app (FastAPI): экземпляр приложения FastAPI.
    """
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="AI Telegram News Generator",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)