import os

from toollib.logu import init_logger as _init_logger

from app.initializer.context import request_id_var


def init_logger(
    level: str,
    serialize: bool = False,
    outdir: str | None = None,
):
    enable_console, enable_file = True, True
    if os.getenv("APP_ENV") == "prod":
        enable_console, enable_file = False, True  # 按需调整
    logger = _init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        enable_console=enable_console,
        enable_file=enable_file,
        outdir=outdir,
    )
    return logger
