from celery_app.consumer import app

app.conf.update(
    task_queues={
        "beat_health": {
            "exchange_type": "direct",
            "exchange": "beat_health",
            "routing_key": "beat_health",
        },
    },
    task_routes={
        "celery_app.consumer.tasks.beat_health.health": {"queue": "beat_health"},
    },
)
