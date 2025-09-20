"""
@author axiner
@version v1.0.0
@created 2025/09/20 10:10
@abstract runcelery（更多参数请自行指定）
@description
@history
"""
import argparse
import platform
import subprocess
from os import cpu_count


def main(
        name: str,
        loglevel: str = "info",
        concurrency: int = None,
        pool: str = None,
):
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", type=str, metavar="", help="名称")
    parser.add_argument("-l", "--loglevel", type=str, default="info", metavar="", help="日志等级")
    parser.add_argument("-c", "--concurrency", type=int, default=None, metavar="", help="并发数")
    parser.add_argument("-P", "--pool", type=str, default=None, metavar="", help="并发模型")
    args = parser.parse_args()
    name = args.name or name
    loglevel = args.loglevel or loglevel
    concurrency = args.concurrency or concurrency
    pool = args.pool or pool
    if pool is None:
        if platform.system().lower().startswith("win"):
            pool = 'gevent'
            if not concurrency:
                concurrency = 100
        else:
            pool = 'prefork'
            if not concurrency:
                concurrency = cpu_count()
    subprocess.run(
        [
            "celery",
            "-A",
            f"app_celery.consumer.workers.{name}",
            "worker",
            f"--loglevel={loglevel}",
            f"--concurrency={concurrency}",
            f"--pool={pool}",
        ],
        check=True,
    )


if __name__ == '__main__':
    main(
        name="aping",
    )
