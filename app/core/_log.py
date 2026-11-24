from toollib.logu import init_logger as _init_logger

from app.core.context import client_ip_var, request_id_var


def init_logger(
    level: str,
    serialize: bool = False,
    enable_console: bool = True,
    enable_file: bool = True,
    outdir: str | None = None,
):
    logger = _init_logger(
        level=level,
        context_vars={"request_id": request_id_var, "client_ip": client_ip_var},
        fmt="%(asctime)s %(levelname)s %(request_id)s %(client_ip)s %(name)s %(filename)s:%(lineno)d %(message)s",
        serialize=serialize,
        enable_console=enable_console,
        enable_file=enable_file,
        outdir=outdir,
    )
    return logger
