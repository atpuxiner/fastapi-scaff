import logging

from celery.schedules import crontab
from celery_app.consumer import app

logger = logging.getLogger(__name__)

app.conf.beat_schedule.setdefault(
    "beat_health",
    {
        "task": "celery_app.consumer.tasks.beat_health.health",
        "schedule": crontab(minute="*/2"),  # 每x分钟执行一次
        "options": {"queue": "beat_health"},
    },
)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    time_limit=360,
    soft_time_limit=300,
    acks_late=True,
)
def health(self, text: str = "这是一个定时任务-健康检测"):
    logger.info(f"OK: {text}")
