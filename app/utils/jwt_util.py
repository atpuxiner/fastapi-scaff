import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt

_JWT_ALGORITHM = "HS256"


def gen_jwt(
    payload: dict,
    key: str,
    typ: Literal["access", "refresh"] = "access",
    exp_seconds: int = 30 * 60,
    algorithm: str = _JWT_ALGORITHM,
) -> str:
    final_payload = payload.copy()
    final_payload.update({
        "typ": typ,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=exp_seconds),
    })
    encoded_jwt = jwt.encode(payload=final_payload, key=key, algorithm=algorithm)
    return encoded_jwt


def verify_jwt(
    token: str,
    key: str = None,
    typ: str = None,
    algorithms: tuple = (_JWT_ALGORITHM,),
) -> dict:
    if not key:
        payload = jwt.decode(jwt=token, options={"verify_signature": False})
    else:
        payload = jwt.decode(jwt=token, key=key, algorithms=algorithms)
    if typ is not None and payload.get("typ") != typ:
        raise ValueError(f"Invalid token type: expected {typ}, got {payload.get('typ')}")
    return payload


def gen_jwt_key(nbytes: int = 32, key: str = None):
    if key:
        return key
    return secrets.token_hex(nbytes)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


if __name__ == '__main__':
    # jkey = gen_jwt_key()
    # print(jkey)
    jkey = "da721f64779fd1d92de7abc2060eb62c7f61cf82942c052007486f759e185f6d"
    jtoken = gen_jwt(
        payload={
            "id": "1",
            "phone": "18900189000",
            "status": 1,
            "role": "admin",
            "name": "admin",
            "age": 18,
            "gender": 1
        },
        key=jkey
    )
    print(jtoken)
