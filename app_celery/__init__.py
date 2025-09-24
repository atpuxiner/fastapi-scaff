"""
@author axiner
@version v0.0.1
@created 2025/09/20 10:10
@abstract app-celery
@description
@history
"""
from celery import Celery

from app_celery.conf import config


def make_celery(include: list = None, configs: dict = None):
    app = Celery(
        main="app_celery",
        broker=config.celery_broker_url,
        backend=config.celery_backend_url,
        include=include,
    )
    app.conf.update(
        timezone=config.celery_timezone,
        enable_utc=config.celery_enable_utc,
        task_serializer=config.celery_task_serializer,
        result_serializer=config.celery_result_serializer,
        accept_content=config.celery_accept_content,
        celery_task_ignore_result=config.celery_task_ignore_result,
        celery_result_expire=config.celery_result_expire,
        celery_task_track_started=config.celery_task_track_started,
        worker_concurrency=config.celery_worker_concurrency,
        worker_prefetch_multiplier=config.celery_worker_prefetch_multiplier,
        worker_max_tasks_per_child=config.celery_worker_max_tasks_per_child,
        broker_connection_retry_on_startup=config.celery_broker_connection_retry_on_startup,
        task_reject_on_worker_lost=config.celery_task_reject_on_worker_lost,
    )
    if configs:
        app.conf.update(configs)
    return app
