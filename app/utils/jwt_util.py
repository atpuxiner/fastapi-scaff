import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt

_JWT_ALGORITHM = "HS256"


def gen_jwt(
    payload: dict,
    jwt_key: str,
    token_type: Literal["access", "refresh"] = "access",
    exp_seconds: int = 30 * 60,
    algorithm: str = _JWT_ALGORITHM,
) -> str:
    final_payload = payload.copy()
    final_payload.update({
        "type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=exp_seconds),
    })
    encoded_jwt = jwt.encode(payload=final_payload, key=jwt_key, algorithm=algorithm)
    return encoded_jwt


def verify_jwt(
    token: str,
    jwt_key: str = None,
    token_type: str = None,
    algorithms: tuple = (_JWT_ALGORITHM,),
) -> dict:
    if not jwt_key:
        payload = jwt.decode(jwt=token, options={"verify_signature": False})
    else:
        payload = jwt.decode(jwt=token, key=jwt_key, algorithms=algorithms)
    if token_type is not None and payload.get("type") != token_type:
        raise ValueError(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
    return payload


def gen_jwt_key(nbytes: int = 32, jwt_key: str = None):
    if jwt_key:
        return jwt_key
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
            "phone": "18810000001",
            "name": "admin",
            "age": 18,
            "gender": 1
        },
        jwt_key=jkey
    )
    print(jtoken)
