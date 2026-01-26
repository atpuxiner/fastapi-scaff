import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt

_JWT_ALGORITHM = "HS256"


def gen_jwt(payload: dict, jwt_key: str, exp_minutes: int = 24 * 60 * 30, algorithm: str = _JWT_ALGORITHM):
    payload.update({"exp": datetime.utcnow() + timedelta(minutes=exp_minutes)})
    encoded_jwt = jwt.encode(payload=payload, key=jwt_key, algorithm=algorithm)
    return encoded_jwt


def verify_jwt(token: str, jwt_key: str = None, algorithms: tuple = (_JWT_ALGORITHM,)) -> dict:
    if not jwt_key:
        return jwt.decode(jwt=token, options={"verify_signature": False})
    return jwt.decode(jwt=token, key=jwt_key, algorithms=algorithms)


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
    # jwt_key = gen_jwt_key()
    # print(jwt_key)
    jwt_key = "da721f64779fd1d92de7abc2060eb62c7f61cf82942c052007486f759e185f6d"
    jwt_token = gen_jwt(
        payload={
            "id": "1",
            "phone": "18810000001",
            "name": "admin",
            "age": 18,
            "gender": 1
        },
        jwt_key=jwt_key
    )
    print(jwt_token)
