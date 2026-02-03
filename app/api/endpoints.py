from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Source, Keyword, NewsItem, Post
from app.api.schemas import (
    SourceIn, SourceOut,
    KeywordIn, KeywordOut,
    NewsOut, PostOut,
    GenerateRequest,
)

from app.ai.ollama_client import OllamaClient
from app.ai.generator import generate_post_text
from app.config import settings
from celery_worker import celery_app

router = APIRouter(prefix="/api", tags=["api"])


# ---------------- Sources CRUD ----------------
@router.get("/sources/", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    """
    Получить список всех источников новостей.

    Args:
        db: Сессия базы данных

    Returns:
        Список всех источников новостей
    """
    return db.scalars(select(Source)).all()


@router.post("/sources/", response_model=SourceOut)
def create_source(payload: SourceIn, db: Session = Depends(get_db)):
    """
    Создать новый источник новостей.

    Args:
        payload: Данные для создания источника
        db: Сессия базы данных

    Returns:
        Созданный источник новостей
    """
    s = Source(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: str, payload: SourceIn, db: Session = Depends(get_db)):
    """
    Обновить существующий источник новостей.

    Args:
        source_id: ID источника для обновления
        payload: Новые данные источника
        db: Сессия базы данных

    Returns:
        Обновленный источник новостей

    Raises:
        HTTPException: Если источник не найден (404)
    """
    s = db.get(Source, source_id)
    if not s:
        raise HTTPException(404, "source not found")
    for k, v in payload.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/sources/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    """
    Удалить источник новостей.

    Args:
        source_id: ID источника для удаления
        db: Сессия базы данных

    Returns:
        Словарь с подтверждением успешного удаления

    Raises:
        HTTPException: Если источник не найден (404)
    """
    s = db.get(Source, source_id)
    if not s:
        raise HTTPException(404, "source not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ---------------- Keywords CRUD ----------------
@router.get("/keywords/", response_model=list[KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    """
    Получить список всех ключевых слов.

    Args:
        db: Сессия базы данных

    Returns:
        Список всех ключевых слов
    """
    return db.scalars(select(Keyword)).all()


@router.post("/keywords/", response_model=KeywordOut)
def create_keyword(payload: KeywordIn, db: Session = Depends(get_db)):
    """
    Создать новое ключевое слово.

    Args:
        payload: Данные для создания ключевого слова
        db: Сессия базы данных

    Returns:
        Созданное ключевое слово

    Raises:
        HTTPException: Если ключевое слово уже существует (400)
    """
    k = Keyword(**payload.model_dump())
    db.add(k)
    try:
        db.commit()
        db.refresh(k)
        return k
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Keyword already exists"
        )


@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """
    Удалить ключевое слово.

    Args:
        keyword_id: ID ключевого слова для удаления
        db: Сессия базы данных

    Returns:
        Словарь с подтверждением успешного удаления

    Raises:
        HTTPException: Если ключевое слово не найдено (404)
    """
    k = db.get(Keyword, keyword_id)
    if not k:
        raise HTTPException(404, "keyword not found")
    db.delete(k)
    db.commit()
    return {"ok": True}


# ---------------- News / Posts ----------------
@router.get("/news/", response_model=list[NewsOut])
def list_news(db: Session = Depends(get_db)):
    """
    Получить список новостей (последние 50).

    Args:
        db: Сессия базы данных

    Returns:
        Список новостей, отсортированных по дате публикации (от новых к старым)
    """
    q = select(NewsItem).order_by(NewsItem.published_at.desc()).limit(50)
    return db.scalars(q).all()


@router.get("/posts/", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    """
    Получить список постов (последние 50).

    Args:
        db: Сессия базы данных

    Returns:
        Список постов, отсортированных по дате создания (от новых к старым)
    """
    q = select(Post).order_by(Post.created_at.desc()).limit(50)
    return db.scalars(q).all()


# ---------------- Manual generation ----------------
@router.post("/generate/")
async def manual_generate(req: GenerateRequest):
    """
    Вручную сгенерировать текст поста на основе новости.

    Args:
        req: Запрос с данными новости (заголовок, краткое содержание, источник, URL)

    Returns:
        Словарь с сгенерированным текстом поста
    """
    ollama = OllamaClient(settings.ollama_base_url, settings.ollama_model)
    text = await generate_post_text(ollama, req.title, req.summary, req.source, req.url)
    return {"generated_text": text}


# ---------------- Run pipeline ----------------
@router.post("/run/")
def run_pipeline():
    """
    Запустить полный пайплайн обработки новостей.

    Отправляет задачу в очередь Celery для асинхронного выполнения
    пайплайна (парсинг новостей, генерация постов и публикация).

    Returns:
        Словарь со статусом задачи и её ID
    """
    task = celery_app.send_task("app.tasks.run_pipeline_task")
    return {
        "status": "queued",
        "task_id": task.id
    }