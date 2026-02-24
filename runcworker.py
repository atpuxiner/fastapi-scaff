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
    name: str,  # `<celery_module>/consumer/workers`下的模块名
    loglevel: str = "info",
    concurrency: int = None,
    pool: str = None,
    celery_module: str = "app_celery",
):
    parser = argparse.ArgumentParser(description="CeleryWorker启动器")
    parser.add_argument("-n", "--name", type=str, metavar="", help="名称")
    parser.add_argument("-l", "--loglevel", type=str, default="info", metavar="", help="日志等级")
    parser.add_argument("-c", "--concurrency", type=int, default=None, metavar="", help="并发数")
    parser.add_argument("-P", "--pool", type=str, default=None, metavar="", help="并发模型")
    parser.add_argument("--celery-module", type=str, default="app_celery", metavar="", help="celery模块")
    args = parser.parse_args()
    name = args.name or name
    loglevel = args.loglevel or loglevel
    concurrency = args.concurrency or concurrency
    pool = args.pool or pool
    celery_module = args.celery_module or celery_module
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
        f"{celery_module}.consumer.workers.{name}",
        "worker",
        f"--loglevel={loglevel}",
        f"--concurrency={concurrency}",
        f"--pool={pool}",
    ]
    subprocess.run(
        command,
        check=True,
    )


if __name__ == '__main__':
    main(
        name="ping",
    )
