# app-celery

## 简介

### producer：生产者（发布任务）

- register：注册中心
  - 将`consumer`的`tasks`注册到`producer`的`register`中
- publisher：发布者
    - 项目中通过发布者来发布任务：可参考`app/api/default/aping.py`（这里只是简单示例，实际上应该在`services`层调用）

### consumer：消费者（执行任务）

- tasks: 任务
  - 定时任务（beat_xxx）
    - 1。创建定时任务
    - 2。发布定时任务（通过celery内部的`beat`调用）
      - 进入`app_celery`父级目录，即工作目录
      - 启动命令：（更多参数请自行指定）
        - 方式1。直接执行脚本: `python runcbeat.py`
        - 方式2。使用命令行：`celery -A app_celery.consumer beat --loglevel=info --max-interval=5`
    - 3。启动消费者worker
  - 异步任务（xxx)
    - 1。创建异步任务，并注册到`producer`的`register`，根据注册的规则进行`任务调用`和`worker启动`
    - 2。发布异步任务（通过生产者的`publisher`调用）
      - 可参考`app/api/default/aping.py`（这里只是简单示例，实际上应该在`services`层调用）
    - 3。启动消费者worker
- workers: 工作者
  - 1。创建worker服务，定义队列等属性（为方便扩展建议一类任务一个服务）
  - 2。启动worker服务：
      - 1。进入`app_celery`父级目录，即工作目录
      - 2。启动命令：（更多参数请自行指定）
          - 方式1。直接执行脚本: `python runcworker.py -n ping`
          - 方式2。使用命令行：`celery -A app_celery.consumer.workers.ping worker --loglevel=info --concurrency=5 --queues=ping`

### 注意：

- 最好与`app`解耦，即：
    - 只有`app`单向调用`app_celery`
    - 但`app_celery`不调用`app`