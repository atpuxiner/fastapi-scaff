from celery_app.consumer import app

app.conf.update(
    task_queues={
        "health": {
            "exchange_type": "direct",
            "exchange": "health",
            "routing_key": "health",
        },
    },
    task_routes={
        "celery_app.consumer.tasks.health.health": {"queue": "health"},
    },
)
