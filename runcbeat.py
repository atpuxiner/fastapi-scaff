"""
@author axiner
@version v1.0.0
@created 2025/09/20 10:10
@abstract runcbeat（更多参数请自行指定）
@description
@history
"""
import argparse
import subprocess


def main(
        loglevel: str = "info",
        scheduler: str = None,
        pidfile: str = None,
        max_interval: int = 5,
        celery_module: str = "app_celery",
):
    parser = argparse.ArgumentParser(description="CeleryBeat启动器")
    parser.add_argument("-l", "--loglevel", type=str, default="info", metavar="", help="日志等级")
    parser.add_argument("-S", "--scheduler", type=str, default=None, metavar="", help="调度器类型")
    parser.add_argument("--pidfile", type=str, default=None, metavar="", help="pid文件")
    parser.add_argument("--max-interval", type=int, default=5, metavar="", help="检测任务间隔")
    args = parser.parse_args()
    loglevel = args.loglevel or loglevel
    scheduler = args.scheduler or scheduler
    pidfile = args.pidfile or pidfile
    max_interval = args.max_interval or max_interval
    command = [
        "celery",
        "-A",
        f"{celery_module}.consumer",
        "beat",
        f"--loglevel={loglevel}",
        f"--max-interval={max_interval}",
    ]
    if scheduler:
        command.extend(["--scheduler", scheduler])
    if pidfile:
        command.extend(["--pidfile", pidfile])
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
