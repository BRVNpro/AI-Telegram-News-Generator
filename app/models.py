"""
Модели базы данных для приложения: NewsItem, Post, Source, Keyword.

Каждый класс соответствует таблице и содержит описание основных полей:
- NewsItem — новости/записи, сохраняемые из источников;
- Post — запись для публикации, связанная с NewsItem;
- Source — источник (RSS/Telegram) с настройкой включения;
- Keyword — ключевые слова для фильтрации новостей.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class NewsItem(Base):
    """
    Таблица `news_items`.

    Поля:
    - id: PK (uuid строка);
    - title: заголовок новости;
    - url: ссылка (опционально);
    - summary: краткое содержание/аннотация;
    - source: источник записи (строка);
    - published_at: время публикации с таймзоной;
    - raw_text: полный необработанный текст (опционально);
    - content_type: тип контента (по умолчанию `'news'`);
    - content_hash: SHA‑256 хэш для дедупликации;
    - created_at: время добавления записи.
    - posts: отношение к записям `Post`.
    """
    __tablename__ = "news_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="news",
    )

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="news_item", cascade="all, delete-orphan"
    )


class Post(Base):
    """
    Таблица `posts` — записи для публикации.

    Поля:
    - id: PK (uuid строка);
    - news_id: FK на `news_items.id`;
    - generated_text: сгенерированный текст поста (опционально);
    - status: статус публикации (`'new'`, `'generated'`, `'published'`, `'failed'` и т.п.);
    - published_at: время публикации (опционально);
    - error: текст ошибки при неудаче (опционально);
    - created_at: время создания записи.
    - news_item: отношение к родительскому `NewsItem`.
    """
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    news_id: Mapped[str] = mapped_column(String, ForeignKey("news_items.id", ondelete="CASCADE"), nullable=False)

    generated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    news_item: Mapped["NewsItem"] = relationship("NewsItem", back_populates="posts")


class Source(Base):
    """
    Таблица `sources` — описывает доступные источники контента.

    Поля:
    - id: PK (uuid строка);
    - type: тип источника (например, `'rss'` или `'tg'`);
    - name: читаемое имя источника;
    - url: адрес источника;
    - enabled: флаг включения/отключения источника.
    """
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Keyword(Base):
    """
    Таблица `keywords` — ключевые слова для фильтрации новостей.

    Поля:
    - id: PK (uuid строка);
    - word: само ключевое слово (уникально).
    """
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    word: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)