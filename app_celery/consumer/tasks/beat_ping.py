import logging

from celery.schedules import crontab

from app_celery.consumer import celery_app

logger = logging.getLogger(__name__)

celery_app.conf.beat_schedule.setdefault(
    'beat_ping', {
        'task': 'app_celery.consumer.tasks.beat_ping.ping',
        'schedule': crontab(minute='*/2'),  # 每x分钟执行一次
        'options': {'queue': 'beat_ping'}
    }
)


@celery_app.task(
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
def ping(self, text: str = "这是一个定时任务测试"):
    logger.info(f"pong: {text}")
