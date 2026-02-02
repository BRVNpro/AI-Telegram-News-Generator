import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db import engine, Base
from app.api.endpoints import router as api_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="AI Telegram News Generator",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)