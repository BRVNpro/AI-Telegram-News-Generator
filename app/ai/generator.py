from __future__ import annotations

from app.ai.ollama_client import OllamaClient

PROMPT_NEWS = """Ты редактор новостного Telegram-канала.
Сгенерируй короткий, яркий пост (до 600 символов) на русском языке по новости ниже.

Требования:
- 1–2 эмодзи в начале
- 2–4 коротких предложения
- в конце 1 call-to-action (вопрос читателю)
- без воды, без повторов
- без ссылок (если ссылка есть — добавь отдельной строкой в конце)

НОВОСТЬ:
Заголовок: {title}
Источник: {source}
Текст/сводка: {summary}
Ссылка: {url}
"""

PROMPT_THOUGHT = """Ты редактор Telegram-канала с размышлениями/лайфстайлом.
Сгенерируй короткий пост (до 600 символов) на русском языке по тексту ниже.

Требования:
- 1–2 эмодзи в начале
- 2–4 коротких предложения
- в конце 1 вопрос читателю
- убрать рекламу/прогрев/призывы записаться/“пиши + в комментариях”
- убрать эзотерику/астрологию/“вибрации” (заменить на нейтральные формулировки)
- без ссылок

ТЕКСТ:
{summary}
"""


def _trim(text: str, limit: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


async def generate_post_text(
    ollama: OllamaClient,
    title: str,
    summary: str,
    source: str,
    url: str | None,
    content_type: str = "news",
) -> str:
    """
    Единая точка генерации текста поста.
    content_type:
      - "news": новостной пост
      - "thought": переработка TG-текста
    """
    if content_type == "thought":
        prompt = PROMPT_THOUGHT.format(summary=summary)
    else:
        prompt = PROMPT_NEWS.format(
            title=title,
            summary=summary,
            source=source,
            url=url or "",
        )

    text = await ollama.generate(prompt)
    return _trim(text)