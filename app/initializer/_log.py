from loguru._logger import Logger  # noqa
from toollib.logu import init_logger as logu_init_logger, LogInterception

from app.initializer.context import request_id_var


def init_logger(
        level: str,
        serialize: bool = False,
        basedir: str = None,
        intercept_standard: bool = False,
) -> Logger:
    interception = None
    if intercept_standard:
        interception = LogInterception
    return logu_init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        basedir=basedir,
        interception=interception,
    )
