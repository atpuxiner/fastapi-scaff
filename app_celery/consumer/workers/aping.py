from app_celery import make_celery

celery_app = make_celery(
    include=[
        "app_celery.consumer.tasks.aping",
    ]
)
celery_app.conf.update(
    task_default_queue="default",
    task_queues={
        "aping": {
            "exchange_type": "direct",
            "exchange": "aping",
            "routing_key": "aping",
        },
    },
    task_routes={
        "app_celery.consumer.tasks.aping": {"queue": "aping"},
    }
)
