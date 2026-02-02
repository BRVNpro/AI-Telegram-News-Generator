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
    workflow = chain(
        parse_sources_task.si(),
        filter_news_task.si(),
        generate_posts_task.s(),
        publish_posts_task.s(),
    )
    res = workflow.apply_async()
    return {"task_id": res.id}