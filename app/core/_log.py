from toollib.logu import init_logger as _init_logger

from app.core.context import request_id_var


def init_logger(
    level: str,
    serialize: bool = False,
    enable_console: bool = True,
    enable_file: bool = True,
    outdir: str | None = None,
):
    logger = _init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        enable_console=enable_console,
        enable_file=enable_file,
        outdir=outdir,
    )
    return logger
