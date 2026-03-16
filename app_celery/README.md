# app-celery

## 简介

### producer：生产者（发布任务）

- register：注册中心
    - 将`consumer`的`tasks`注册到`producer`的`register`中
- publisher：发布者
    - 项目中通过`publisher.publish`来发布任务

### consumer：消费者（执行任务）

- tasks: 任务
    - 定时任务（beat_xxx）
        - 1。创建定时任务
        - 2。发布定时任务（通过celery内部的`beat`调用）
            - 进入`app_celery`父级目录，即工作目录
            - 启动命令：（更多参数请自行指定）
                - 方式1。直接执行脚本: `python runcbeat.py --celery-module=app_celery`
                - 方式2。使用命令行：`celery -A app_celery.consumer beat --loglevel=info --max-interval=5`
        - 3。启动消费者worker
    - 异步任务（xxx)
        - 1。创建异步任务，并注册到`producer`的`register`，根据注册的规则进行`任务调用`和`worker启动`
        - 2。发布异步任务（通过生产者的`publisher.publish`调用）
        - 3。启动消费者worker
- workers: 工作者
    - 1。创建worker服务，定义队列等属性（为方便扩展建议一类任务一个服务）
    - 2。启动worker服务：
        - 1。进入`app_celery`父级目录，即工作目录
        - 2。启动命令：（更多参数请自行指定）
            - 方式1。直接执行脚本: `python runcworker.py -n ping --celery-module=app_celery`
            - 方式2。使用命令行：`celery -A app_celery.consumer.workers.ping worker --loglevel=info --concurrency=5`
- yaml配置

```yaml
CELERY_BROKER_URL: redis://:<password>@<host>:<port>/<db>
CELERY_BACKEND_URL: redis://:<password>@<host>:<port>/<db>
CELERY_TIMEZONE: Asia/Shanghai
CELERY_ENABLE_UTC: true
CELERY_TASK_SERIALIZER: json
CELERY_RESULT_SERIALIZER: json
CELERY_ACCEPT_CONTENT: [json]
CELERY_TASK_IGNORE_RESULT: false
CELERY_RESULT_EXPIRE: 86400
CELERY_TASK_TRACK_STARTED: true
CELERY_WORKER_CONCURRENCY: 8
CELERY_WORKER_PREFETCH_MULTIPLIER: 2
CELERY_WORKER_MAX_TASKS_PER_CHILD: 100
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: true
CELERY_TASK_REJECT_ON_WORKER_LOST: true
```

- 消费端依赖

```text
celery
redis
```

### 注意：

- 最好与`app`解耦，即：
    - 只`app`单向调用`app_celery`
    - 但`app_celery`不调用`app`
