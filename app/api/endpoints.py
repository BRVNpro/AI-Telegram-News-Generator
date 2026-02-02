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
    return db.scalars(select(Source)).all()


@router.post("/sources/", response_model=SourceOut)
def create_source(payload: SourceIn, db: Session = Depends(get_db)):
    s = Source(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: str, payload: SourceIn, db: Session = Depends(get_db)):
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
    s = db.get(Source, source_id)
    if not s:
        raise HTTPException(404, "source not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ---------------- Keywords CRUD ----------------
@router.get("/keywords/", response_model=list[KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    return db.scalars(select(Keyword)).all()


@router.post("/keywords/", response_model=KeywordOut)
def create_keyword(payload: KeywordIn, db: Session = Depends(get_db)):
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
    k = db.get(Keyword, keyword_id)
    if not k:
        raise HTTPException(404, "keyword not found")
    db.delete(k)
    db.commit()
    return {"ok": True}


# ---------------- News / Posts ----------------
@router.get("/news/", response_model=list[NewsOut])
def list_news(db: Session = Depends(get_db)):
    q = select(NewsItem).order_by(NewsItem.published_at.desc()).limit(50)
    return db.scalars(q).all()


@router.get("/posts/", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    q = select(Post).order_by(Post.created_at.desc()).limit(50)
    return db.scalars(q).all()


# ---------------- Manual generation ----------------
@router.post("/generate/")
async def manual_generate(req: GenerateRequest):
    ollama = OllamaClient(settings.ollama_base_url, settings.ollama_model)
    text = await generate_post_text(ollama, req.title, req.summary, req.source, req.url)
    return {"generated_text": text}


# ---------------- Run pipeline ----------------
@router.post("/run/")
def run_pipeline():
    task = celery_app.send_task("app.tasks.run_pipeline_task")
    return {
        "status": "queued",
        "task_id": task.id
    }