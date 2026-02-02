import os
from dotenv import load_dotenv

load_dotenv()

from celery import Celery

celery_app = Celery(
    "aibot",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

# 🔥 ВОТ ЭТО КЛЮЧ
celery_app.autodiscover_tasks(["app"])

celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    "run-pipeline-every-30-min": {
        "task": "app.tasks.run_pipeline_task",
        "schedule": 30 * 60,
    }
}