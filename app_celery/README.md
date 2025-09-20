# app-celery

## 简介

### producer：生产者

- register：注册中心
- publisher：发布者
    - 项目中通过发布者来发布任务：可参考`app/api/default/aping.py`(这里只是简单示例，实际上应该在`services`层调用)

### consumer：消费者

- tasks: 任务
- workers: 工作者
- 启动：这里最好一类任务一个服务，这样方便扩展
    - 1。进入`app_celery`父级目录，即工作目录
    - 2。启动命令
        - 方式1。直接执行脚本: `python runcelery.py -n aping`
        - 方式2。使用命令行(注意`queue`)：`celery -A app_celery.consumer.workers.aping worker --queues=aping --loglevel=info --concurrency=5`

### 注意：

- 最好与`app`解耦，即：
    - 只有`app`单向调用`app_celery`下的生产者`producer`
    - 但`app_celery`不调用`app`