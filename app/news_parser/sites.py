from datetime import datetime, timezone
import feedparser

from app.utils import normalize_text


def parse_rss(feed_url: str, source_name: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    items: list[dict] = []

    for e in feed.entries[:30]:
        title = normalize_text(getattr(e, "title", "") or "")
        url = getattr(e, "link", None)
        summary = normalize_text(getattr(e, "summary", "") or getattr(e, "description", "") or "")

        published_parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        if published_parsed:
            dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        if not title or not summary:
            continue

        items.append(
            {
                "title": title,
                "url": url,
                "summary": summary[:1500],
                "source": source_name,
                "published_at": dt,
                "raw_text": None,
            }
        )

    return items