import uuid
from toollib.utils import now2timestamp


def gen_uuid_hex():
    return uuid.uuid4().hex


def now_timestamp():
    return now2timestamp()
