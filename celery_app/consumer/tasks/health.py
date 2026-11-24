import logging

from celery_app.consumer import app

logger = logging.getLogger(__name__)


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
def health(self, text: str = "这是一个异步任务-健康检测"):
    logger.info(f"OK: {text}")
