from datetime import datetime
from pydantic import BaseModel


class SourceIn(BaseModel):
    type: str
    name: str
    url: str
    enabled: bool = True


class SourceOut(SourceIn):
    id: str


class KeywordIn(BaseModel):
    word: str


class KeywordOut(KeywordIn):
    id: str


class NewsOut(BaseModel):
    id: str
    title: str
    url: str | None
    summary: str
    source: str
    published_at: datetime


class PostOut(BaseModel):
    id: str
    news_id: str
    generated_text: str | None
    status: str
    published_at: datetime | None
    error: str | None
    created_at: datetime


class GenerateRequest(BaseModel):
    title: str
    summary: str
    source: str = "manual"
    url: str | None = None