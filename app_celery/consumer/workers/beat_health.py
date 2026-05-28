from app_celery.consumer import celery_app

celery_app.conf.update(
    task_queues={
        "beat_health": {
            "exchange_type": "direct",
            "exchange": "beat_health",
            "routing_key": "beat_health",
        },
    },
    task_routes={
        "app_celery.consumer.tasks.beat_health.health": {"queue": "beat_health"},
    },
)
