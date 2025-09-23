import logging

from app_celery.consumer import celery_app

logger = logging.getLogger(__name__)


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
def ping(self, text: str = "这是一个异步任务测试"):
    logger.info(f"pong: {text}")
