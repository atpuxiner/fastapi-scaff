import os
import sys
from pathlib import Path

from loguru import logger
from loguru._logger import Logger  # noqa

from app.initializer.context import request_id_ctx_var

_LOG_CONSOLE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {extra[request_id]} {file}:{line} {message}"
_LOG_FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {extra[request_id]} {file}:{line} {message}"
_LOG_FILE_PREFIX = "app"
_LOG_ROTATION = "100 MB"
_LOG_RETENTION = "15 days"
_LOG_COMPRESSION = None
_LOG_ENQUEUE = True
_LOG_BACKTRACE = False
_LOG_DIAGNOSE = False
_LOG_PID = False


def init_logger(
        debug: bool,
        log_dir: str = None,
) -> Logger:
    logger.remove(None)
    _lever = "DEBUG" if debug else "INFO"

    def _filter(record: dict) -> bool:
        record["extra"]["request_id"] = request_id_ctx_var.get()
        return True

    logger.add(
        sys.stdout,
        format=_LOG_CONSOLE_FORMAT,
        level=_lever,
        enqueue=_LOG_ENQUEUE,
        backtrace=_LOG_BACKTRACE,
        diagnose=_LOG_DIAGNOSE,
        filter=_filter,
    )
    if log_dir:
        _log_dir = Path(log_dir)
        _log_access_file = _log_dir.joinpath(f"{_LOG_FILE_PREFIX}-access.log")
        _log_error_file = _log_dir.joinpath(f"{_LOG_FILE_PREFIX}-error.log")
        if _LOG_PID:
            _log_access_file = str(_log_access_file).replace(".log", f".{os.getpid()}.log")
            _log_error_file = str(_log_error_file).replace(".log", f".{os.getpid()}.log")
        logger.add(
            _log_access_file,
            encoding="utf-8",
            format=_LOG_FILE_FORMAT,
            level=_lever,
            rotation=_LOG_ROTATION,
            retention=_LOG_RETENTION,
            compression=_LOG_COMPRESSION,
            enqueue=_LOG_ENQUEUE,
            backtrace=_LOG_BACKTRACE,
            diagnose=_LOG_DIAGNOSE,
        )
        logger.add(
            _log_error_file,
            encoding="utf-8",
            format=_LOG_FILE_FORMAT,
            level="ERROR",
            rotation=_LOG_ROTATION,
            retention=_LOG_RETENTION,
            compression=_LOG_COMPRESSION,
            enqueue=_LOG_ENQUEUE,
            backtrace=_LOG_BACKTRACE,
            diagnose=_LOG_DIAGNOSE,
        )
    return logger
