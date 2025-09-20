import logging

from app_celery import make_celery

logger = logging.getLogger(__name__)

celery_app = make_celery()


@celery_app.task(
    name="aping",
)
def aping(text: str):
    logger.info(f"apong: {text}")
