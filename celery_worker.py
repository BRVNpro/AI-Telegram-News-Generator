# python
"""
Модуль `celery_worker` — настройка и создание экземпляра Celery для проекта.

Этот модуль:
- загружает переменные окружения через `.env`,
- создаёт экземпляр Celery с брокером и бэкендом, взятыми из окружения,
- включает автоматическое обнаружение тасков в пакете `app`,
- настраивает часовой пояс и расписание периодических задач (beat).

Переменная `celery_app` содержит готовый к использованию объект Celery.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from celery import Celery


def create_celery(app_name: str = "aibot") -> Celery:
    """
    Создаёт и настраивает экземпляр Celery.

    Args:
        app_name (str): Имя приложения Celery. По умолчанию "aibot".

    Returns:
        Celery: Настроенный экземпляр Celery с автодискавером тасков и расписанием.
    """
    celery = Celery(
        app_name,
        broker=os.getenv("CELERY_BROKER_URL"),
        backend=os.getenv("CELERY_RESULT_BACKEND"),
    )

    celery.autodiscover_tasks(["app"])
    celery.conf.timezone = "UTC"
    celery.conf.beat_schedule = {
        "run-pipeline-every-30-min": {
            "task": "app.tasks.run_pipeline_task",
            "schedule": 30 * 60,
        }
    }

    return celery


celery_app = create_celery()