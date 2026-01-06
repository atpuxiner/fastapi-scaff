"""
@author axiner
@version v1.0.0
@created 2024/07/29 22:22
@abstract runserver（更多参数请自行指定）
@description
@history
"""
import argparse
import subprocess
import sys

import uvicorn


def run_by_unicorn(
        host: str,
        port: int,
        workers: int,
        log_level: str,
        reload: bool,
):
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",
                "use_colors": None
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": "%(asctime)s %(levelname)s %(client_addr)s - \"%(request_line)s\" %(status_code)s"
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr"
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "uvicorn": {
                "handlers": [
                    "default"
                ],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO"
            },
            "uvicorn.access": {
                "handlers": [
                    "access"
                ],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    uvicorn.run(
        app="app.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        log_config=log_config,
        reload=reload,
    )


def run_by_gunicorn(
        host: str,
        port: int,
        workers: int,
        log_level: str,
        reload: bool,
):
    cmd = (
        "gunicorn app.main:app "
        "--worker-class=uvicorn.workers.UvicornWorker "
        "--bind={host}:{port} "
        "--workers={workers} "
        "--log-level={log_level} "
        "--access-logfile=- "
        "--error-logfile=-"
        .format(
            host=host,
            port=port,
            workers=workers,
            log_level=log_level,
        )
    )
    if reload:
        cmd += f" --reload"
    subprocess.run(cmd, shell=True)


def main(
        host: str,
        port: int,
        workers: int,
        log_level: str,
        reload: bool,
        gunicorn: bool,
):
    parser = argparse.ArgumentParser(description="App启动器")
    parser.add_argument("--host", type=str, metavar="", help="host")
    parser.add_argument("--port", type=int, metavar="", help="port")
    parser.add_argument("--workers", type=int, metavar="", help="进程数")
    parser.add_argument("--log-level", type=str, metavar="", help="日志等级")
    parser.add_argument("--reload", action="store_true", help="是否reload")
    parser.add_argument("--gunicorn", action="store_true", help="是否gunicorn")
    args = parser.parse_args()
    kwargs = {
        "host": args.host or host,
        "port": args.port or port,
        "workers": args.workers or workers,
        "log_level": args.log_level or log_level,
        "reload": args.reload or reload,
    }
    if (args.gunicorn or gunicorn) and not sys.platform.lower().startswith("win"):
        try:
            import gunicorn  # noqa
        except ImportError:
            sys.stderr.write("gunicorn未找到，正在尝试自动安装...\n")
            try:
                subprocess.run(
                    ["pip", "install", "gunicorn"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                sys.stderr.write("gunicorn安装成功\n")
            except subprocess.CalledProcessError as e:
                sys.stderr.write(f"gunicorn安装失败: {e.stderr.decode().strip()}\n")
                raise
        run_by_gunicorn(**kwargs)
    else:
        run_by_unicorn(**kwargs)


if __name__ == '__main__':
    main(
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="debug",
        reload=False,  # For development environment
        gunicorn=False,  # Not supported on Windows
    )
