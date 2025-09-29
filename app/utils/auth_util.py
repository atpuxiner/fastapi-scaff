import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt

_ALGORITHM = "HS256"


def gen_jwt(payload: dict, jwt_key: str, exp_minutes: int = 24 * 60 * 30):
    payload.update({"exp": datetime.utcnow() + timedelta(minutes=exp_minutes)})
    encoded_jwt = jwt.encode(payload=payload, key=jwt_key, algorithm=_ALGORITHM)
    return encoded_jwt


def verify_jwt(token: str, jwt_key: str = None) -> dict:
    if not jwt_key:
        return jwt.decode(jwt=token, options={"verify_signature": False})
    return jwt.decode(jwt=token, key=jwt_key, algorithms=[_ALGORITHM])


def gen_jwt_key():
    return secrets.token_hex(16)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
