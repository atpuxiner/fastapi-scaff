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


def make_celery(include: list | None = None, configs: dict | None = None):
    app = Celery(
        main="app_celery",
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_BACKEND_URL,
        include=include,
    )
    app.conf.update(
        timezone=config.CELERY_TIMEZONE,
        enable_utc=config.CELERY_ENABLE_UTC,
        task_serializer=config.CELERY_TASK_SERIALIZER,
        result_serializer=config.CELERY_RESULT_SERIALIZER,
        accept_content=config.CELERY_ACCEPT_CONTENT,
        celery_task_ignore_result=config.CELERY_TASK_IGNORE_RESULT,
        celery_result_expire=config.CELERY_RESULT_EXPIRE,
        celery_task_track_started=config.CELERY_TASK_TRACK_STARTED,
        worker_concurrency=config.CELERY_WORKER_CONCURRENCY,
        worker_prefetch_multiplier=config.CELERY_WORKER_PREFETCH_MULTIPLIER,
        worker_max_tasks_per_child=config.CELERY_WORKER_MAX_TASKS_PER_CHILD,
        broker_connection_retry_on_startup=config.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
        task_reject_on_worker_lost=config.CELERY_TASK_REJECT_ON_WORKER_LOST,
    )
    if configs:
        app.conf.update(configs)
    return app
