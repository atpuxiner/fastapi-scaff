"""
@author axiner
@version v1.0.0
@created 2025/09/20 10:10
@abstract runcworker（更多参数请自行指定）
@description
@history
"""
import argparse
import platform
import subprocess
from os import cpu_count


def main(
        name: str,  # `app_celery/consumer/workers`下的模块名
        loglevel: str = "info",
        concurrency: int = None,
        pool: str = None,
        queues: str = None,
):
    parser = argparse.ArgumentParser(description="CeleryWorker启动器")
    parser.add_argument("-n", "--name", type=str, metavar="", help="名称")
    parser.add_argument("-l", "--loglevel", type=str, default="info", metavar="", help="日志等级")
    parser.add_argument("-c", "--concurrency", type=int, default=None, metavar="", help="并发数")
    parser.add_argument("-P", "--pool", type=str, default=None, metavar="", help="并发模型")
    parser.add_argument("-Q", "--queues", type=str, default=None, metavar="", help="队列")
    args = parser.parse_args()
    name = args.name or name
    loglevel = args.loglevel or loglevel
    concurrency = args.concurrency or concurrency
    pool = args.pool or pool
    queues = args.queues or queues
    if pool is None:
        if platform.system().lower().startswith("win"):
            pool = 'gevent'
            if not concurrency:
                concurrency = 100
        else:
            pool = 'prefork'
            if not concurrency:
                concurrency = cpu_count()
    command = [
        "celery",
        "-A",
        f"app_celery.consumer.workers.{name}",
        "worker",
        f"--loglevel={loglevel}",
        f"--concurrency={concurrency}",
        f"--pool={pool}",
    ]
    if queues:
        command.extend(["--queues", queues])
    subprocess.run(
        command,
        check=True,
    )


if __name__ == '__main__':
    main(
        name="ping",
    )
