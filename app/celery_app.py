from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

   beat_schedule={
    "send-daily-digest": {
        "task": "app.tasks.send_daily_digest",
        "schedule": 60.0,  # runs every 60 seconds for testing
    }
}
)