# python
"""
Модуль `app.tasks` — Celery‑таски для полного пайплайна обработки новостей.

Этот модуль выполняет:
- парсинг источников (RSS и Telegram) и сохранение новостей в БД;
- фильтрацию новостей по ключевым словам и создание записей для публикации;
- генерацию текста постов с помощью Ollama и сохранение результатов;
- публикацию сгенерированных постов в Telegram;
- оркестрацию шагов в виде цепочки задач.

Каждая функция, помеченная `@shared_task`, возвращает данные, указанные в её докстринге
(например, количество добавленных записей или список идентификаторов).
"""
import logging
from datetime import datetime, timezone

from celery import chain, shared_task
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db import SessionLocal
from app.models import NewsItem, Post, Keyword
from app.utils import make_hash, matches_keywords

from app.news_parser.sites import parse_rss
from telethon import TelegramClient
from app.news_parser.telegram import parse_telegram_channel

from app.ai.ollama_client import OllamaClient
from app.ai.generator import generate_post_text
from app.telegram.publisher import publish_text

logger = logging.getLogger(__name__)


from telethon.errors import FloodWaitError
import asyncio

MAX_POSTS_PER_RUN = 5
POST_DELAY = 60


def run_async(coro):
    """
    Выполнить asyncio‑корутину в подходящем цикле событий и вернуть результат.

    Функция безопасно запускает корутину как в чужом, так и в собственном
    цикле событий: если текущий цикл уже запущен, создаётся временный цикл.

    Args:
        coro: awaitable — корутина или awaitable объект.

    Returns:
        Любое: результат выполнения корутины.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    return asyncio.run(coro)


@shared_task
def parse_sources_task() -> int:
    """
    Спарсить RSS и Telegram источник и сохранить новые записи в таблицу `NewsItem`.

    Логика:
    - парсит RSS через `parse_rss` и Telegram канал через `parse_telegram_channel`;
    - формирует `content_hash` через `make_hash` для дедупликации;
    - добавляет новые `NewsItem` в БД, игнорируя уже существующие записи
      (через обработку `IntegrityError`).

    Returns:
        int: количество добавленных записей.
    """
    db = SessionLocal()
    added = 0
    try:
        rss_items = parse_rss(settings.rss_feed_url, source_name="rss:habr")
        async def _tg():
            async with TelegramClient(
                settings.tg_session_name,
                settings.tg_api_id,
                settings.tg_api_hash,
            ) as client:
                items = await parse_telegram_channel(
                    client,
                    settings.tg_source_channel,
                    source_name="tg:source",
                    content_type="thought",
                )
                return items

        tg_items = run_async(_tg())
        all_items = rss_items + tg_items

        for it in all_items:
            content_hash = make_hash(
                it["source"],
                it["title"],
                it.get("url") or "",
                it["summary"],
            )
            ni = NewsItem(
                title=it["title"],
                url=it.get("url"),
                summary=it["summary"],
                source=it["source"],
                published_at=it["published_at"],
                raw_text=it.get("raw_text"),
                content_type=it.get("content_type", "news"),
                content_hash=content_hash,
            )
            db.add(ni)
            try:
                db.commit()
                added += 1
            except IntegrityError:
                db.rollback()
                continue

        logger.info("parse_sources_task: added=%s", added)
        return added
    finally:
        db.close()


@shared_task
def filter_news_task() -> list[str]:
    """
    Отфильтровать недавно добавленные `NewsItem` и создать записи `Post` для публикации.

    Логика:
    - загружает ключевые слова из таблицы `Keyword`;
    - выбирает последние 50 новостей и применяет `matches_keywords` к тексту;
    - создаёт запись `Post` со статусом `"new"` для новостей, которых ещё нет в `Post`.

    Returns:
        list[str]: список идентификаторов созданных записей `Post`.
    """
    db = SessionLocal()
    try:
        keywords = [k.word for k in db.scalars(select(Keyword)).all()]

        q = select(NewsItem).order_by(NewsItem.published_at.desc()).limit(50)
        news = db.scalars(q).all()

        post_ids: list[str] = []
        for n in news:
            if n.content_type == "news":
                text = f"{n.title}\n{n.summary}"
                if not matches_keywords(text, keywords):
                    continue

            exists = db.scalar(select(Post).where(Post.news_id == n.id))
            if exists:
                continue

            p = Post(news_id=n.id, status="new")
            db.add(p)
            db.commit()
            post_ids.append(p.id)

        logger.info("filter_news_task: posts=%s", len(post_ids))
        return post_ids
    finally:
        db.close()


@shared_task
def generate_posts_task(post_ids: list[str]) -> list[str]:
    """
    Сгенерировать текст для списка постов с помощью Ollama и сохранить результаты.

    Логика:
    - для каждого `Post` со статусом `"new"` получает связанный `NewsItem`;
    - вызывает `generate_post_text` (асинхронно) и сохраняет `generated_text`;
    - при успехе устанавливает статус `"generated"`, при ошибке — `"failed"` с текстом ошибки.

    Args:
        post_ids (list[str]): список идентификаторов `Post` для генерации.

    Returns:
        list[str]: список идентификаторов постов, успешно обновлённых (`generated`).
    """
    if not post_ids:
        return []

    db = SessionLocal()
    try:
        async def _gen():
            ollama = OllamaClient(settings.ollama_base_url, settings.ollama_model)
            updated: list[str] = []

            for pid in post_ids:
                post = db.get(Post, pid)
                if not post or post.status != "new":
                    continue
                news = db.get(NewsItem, post.news_id)
                if not news:
                    continue

                try:
                    text = await generate_post_text(
                        ollama=ollama,
                        title=news.title,
                        summary=news.summary,
                        source=news.source,
                        url=news.url,
                        content_type=getattr(news, "content_type", "news"),
                    )
                    post.generated_text = text
                    post.status = "generated"
                    post.error = None
                    db.commit()
                    updated.append(pid)
                except Exception as e:
                    post.status = "failed"
                    post.error = f"generate_error: {e}"
                    db.commit()

            return updated

        return run_async(_gen())
    finally:
        db.close()


@shared_task
def publish_posts_task(post_ids: list[str]) -> int:
    """
    Опубликовать сгенерированные посты в целевой Telegram‑канал.

    Логика:
    - открывает сессию Telethon и публикует не более `MAX_POSTS_PER_RUN` постов;
    - после каждой успешной публикации делает `await asyncio.sleep(POST_DELAY)`;
    - при `FloodWaitError` делает паузу на `e.seconds + 5` и прерывает цикл;
    - обновляет статус поста (`published` / `failed`) и проставляет `published_at`.

    Args:
        post_ids (list[str]): список идентификаторов `Post` для публикации.

    Returns:
        int: количество успешно опубликованных постов.
    """
    if not post_ids:
        return 0

    db = SessionLocal()
    try:
        async def _pub():
            async with TelegramClient(
                settings.tg_session_name,
                settings.tg_api_id,
                settings.tg_api_hash,
            ) as client:
                published = 0

                for pid in post_ids[:MAX_POSTS_PER_RUN]:
                    post = db.get(Post, pid)
                    if not post or post.status != "generated" or not post.generated_text:
                        continue

                    try:
                        await publish_text(
                            client,
                            settings.tg_target_channel,
                            post.generated_text,
                        )

                        post.status = "published"
                        post.published_at = datetime.now(timezone.utc)
                        post.error = None
                        db.commit()
                        published += 1

                        await asyncio.sleep(POST_DELAY)

                    except FloodWaitError as e:
                        logger.warning(f"FloodWait {e.seconds}s — sleeping")
                        await asyncio.sleep(e.seconds + 5)
                        break

                    except Exception as e:
                        post.status = "failed"
                        post.error = f"publish_error: {e}"
                        db.commit()

                return published

        return run_async(_pub())
    finally:
        db.close()


@shared_task
def run_pipeline_task() -> dict:
    """
    Запустить весь пайплайн в виде цепочки Celery задач:
    parse_sources_task -> filter_news_task -> generate_posts_task -> publish_posts_task.

    Returns:
        dict: словарь с ключом `task_id` — идентификатором запущенного рабочего процесса.
    """
    workflow = chain(
        parse_sources_task.si(),
        filter_news_task.si(),
        generate_posts_task.s(),
        publish_posts_task.s(),
    )
    res = workflow.apply_async()
    return {"task_id": res.id}