# AI Telegram News Generator

## Описание проекта

AI Telegram News Generator — это сервис для автоматизации новостного Telegram-канала.
Он собирает новости из RSS-лент и публичных Telegram-каналов, фильтрует их по ключевым словам,
генерирует короткие посты с помощью AI и публикует их в Telegram по расписанию.

Проект реализован в рамках учебного задания Project M4-2.

## Функциональные возможности

- Сбор новостей с сайтов (RSS)
- Чтение сообщений из публичных Telegram-каналов
- Фильтрация новостей по ключевым словам
- Исключение дубликатов
- Генерация постов с помощью AI
- Публикация в Telegram-канал
- Автоматический запуск по расписанию (Celery Beat)
- REST API для управления источниками и ключевыми словами
- История новостей и постов
- Ручная генерация постов через API

## Используемые технологии

- Python 3.13
- FastAPI
- SQLAlchemy
- Celery
- Redis
- Telethon
- Ollama (LLM)
- PostgreSQL / SQLite

## Структура проекта
```
Parsingbot/
├── app/
│   ├── main.py
│   ├── api/
│   ├── news_parser/
│   ├── ai/
│   ├── telegram/
│   ├── tasks.py
│   ├── models.py
│   ├── config.py
│   ├── db.py
│   └── utils.py
├── celery_worker.py
├── auth_telethon.py
├── requirements.txt
├── README.md
└── .env.example
```


## Модели данных

NewsItem:
- id
- title
- url
- summary
- source
- published_at
- raw_text
- content_type
- content_hash

Post:
- id
- news_id
- generated_text
- status
- published_at
- error

Source:
- id
- type
- name
- url
- enabled

Keyword:
- id
- word

---

## Переменные окружения
```
DATABASE_URL
REDIS_URL
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
OLLAMA_BASE_URL
OLLAMA_MODEL
TG_API_ID
TG_API_HASH
TG_SESSION_NAME
TG_SOURCE_CHANNEL
TG_TARGET_CHANNEL
RSS_FEED_URL
```


## Запуск проекта

pip install -r requirements.txt
python auth_telethon.py
redis-server
uvicorn app.main:app --reload

Swagger доступен по адресу:
http://localhost:8000/docs

---

## Celery

celery -A celery_worker.celery_app worker -B -l info

---

## Соответствие ТЗ

Все основные требования Project M4-2 реализованы:
- сбор данных
- очередь задач
- AI-генерация
- публикация
- REST API
- документация
