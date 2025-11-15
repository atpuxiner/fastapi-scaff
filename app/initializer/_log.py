from loguru._logger import Logger  # noqa
from toollib import logu

from app.initializer.context import request_id_var


def init_logger(
        level: str,
        serialize: bool = False,
        basedir: str = None,
) -> Logger:
    return logu.init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        basedir=basedir,
    )
