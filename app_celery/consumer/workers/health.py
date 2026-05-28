from app_celery.consumer import celery_app

celery_app.conf.update(
    task_queues={
        "health": {
            "exchange_type": "direct",
            "exchange": "health",
            "routing_key": "health",
        },
    },
    task_routes={
        "app_celery.consumer.tasks.health.health": {"queue": "health"},
    },
)
