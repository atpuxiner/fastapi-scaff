import os

from loguru._logger import Logger  # noqa
from toollib import logu

from app.initializer.context import request_id_var


def init_logger(
        level: str,
        serialize: bool = False,
        basedir: str = None,
) -> Logger:
    enable_console, enable_file = True, True
    if os.getenv("app_env") == "prod":
        enable_console, enable_file = False, True  # 按需调整
    _logger = logu.init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        enable_console=enable_console,
        enable_file=enable_file,
        basedir=basedir,
    )
    # _logger.add 可添加其他 handler
    return _logger
