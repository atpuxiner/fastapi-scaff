from app_celery.consumer import celery_app

celery_app.conf.update(
    task_queues={
        "ping": {
            "exchange_type": "direct",
            "exchange": "ping",
            "routing_key": "ping",
        },
    },
    task_routes={
        "app_celery.consumer.tasks.ping.ping": {"queue": "ping"},
    }
)
