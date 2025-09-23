from app_celery.consumer import celery_app

celery_app.conf.update(  # 建议所有的定时任务都放在这个worker中启动
    task_queues={
        "beat_ping": {
            "exchange_type": "direct",
            "exchange": "beat_ping",
            "routing_key": "beat_ping",
        },
    },
    task_routes={
        "app_celery.consumer.tasks.beat_ping.ping": {"queue": "beat_ping"},
    }
)
