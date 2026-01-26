import uuid
from toollib.utils import now2timestamp

from app.initializer import g


def gen_uuid_hex() -> str:
    return uuid.uuid4().hex


def gen_snow_id(to_str: bool = True):
    return g.snow_cli.gen_uid(to_str=to_str)


def now_timestamp() -> int:
    return now2timestamp()
