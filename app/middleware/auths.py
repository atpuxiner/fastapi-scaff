from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional

from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
from starlette.requests import Request

from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.utils import db_async_util
from app.utils.auths_util import verify_jwt


# ======= jwt =======

class JWTUser(BaseModel):
    # 与实际`user`对齐
    id: str = None
    phone: str = None
    name: str = None
    age: int = None
    gender: int = None

    @staticmethod
    async def get_user_jwt_key(user_id: str) -> str:
        # 建议：jwt_key进行redis缓存
        async with g.db_async_session() as session:
            data = await db_async_util.sqlfetch_one(
                session=session,
                sql='SELECT jwt_key FROM "user" WHERE id = :id',  # noqa
                params={"id": user_id},
            )
            return data.get("jwt_key")


class JWTAuthorizationCredentials(HTTPAuthorizationCredentials):
    jwt_user: JWTUser


class JWTBearer(HTTPBearer):

    async def __call__(
            self, request: Request
    ) -> Optional[JWTAuthorizationCredentials]:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise CustomException(
                    msg="Not authenticated",
                    status=Status.UNAUTHORIZED_ERROR,
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise CustomException(
                    msg="Invalid authentication credentials",
                    status=Status.UNAUTHORIZED_ERROR,
                )
            else:
                return None
        jwt_user = await self.verify_credentials(credentials)
        return JWTAuthorizationCredentials(scheme=scheme, credentials=credentials, jwt_user=jwt_user)

    async def verify_credentials(self, credentials: str) -> JWTUser:
        playload = await self._verify_jwt(credentials)
        if playload is None:
            raise CustomException(status=Status.UNAUTHORIZED_ERROR)
        user_jwt_key = await JWTUser.get_user_jwt_key(playload.get("id"))
        if not user_jwt_key:
            raise CustomException(status=Status.UNAUTHORIZED_ERROR)
        await self._verify_jwt(credentials, jwt_key=user_jwt_key)
        return JWTUser(
            id=playload.get("id"),
            phone=playload.get("phone"),
            name=playload.get("name"),
            age=playload.get("age"),
            gender=playload.get("gender"),
        )

    @staticmethod
    async def _verify_jwt(token: str, jwt_key: str = None) -> dict:
        try:
            return verify_jwt(token=token, jwt_key=jwt_key)
        except Exception as e:
            raise CustomException(status=Status.UNAUTHORIZED_ERROR, msg=str(e))


def get_current_user(
        credentials: Optional[JWTAuthorizationCredentials] = Depends(JWTBearer(auto_error=True))
) -> JWTUser:
    if not credentials:
        return JWTUser()
    return credentials.jwt_user


# ======= api key =======

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class ApiKeyUser(BaseModel):

    @staticmethod
    def get_user_api_key(user_id: str = None) -> list:
        if user_id:
            return g.config.api_keys.get(user_id)
        return g.config.api_keys


async def get_current_api_key(api_key: str = Security(_API_KEY_HEADER)):
    if not api_key:
        raise CustomException(status=Status.FORBIDDEN_ERROR)
    user_api_key = ApiKeyUser.get_user_api_key()
    if not user_api_key:
        raise CustomException(status=Status.UNAUTHORIZED_ERROR)
    if api_key not in user_api_key:
        raise CustomException(status=Status.UNAUTHORIZED_ERROR)
    return api_key
