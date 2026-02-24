from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.sql.elements import quoted_name
from starlette.requests import Request

from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.utils.jwt_util import verify_jwt


# -------------------- jwt --------------------

_REFRESH_TOKEN_COOKIE_NAME = "x_refresh_token"


class JWTUser(BaseModel):
    # 与实际字段对齐
    id: str = None
    phone: str = None
    status: int = None
    role: str = None
    name: str = None
    age: int = None
    gender: int = None

    @staticmethod
    async def get_user_jwt_key(user_id: str) -> str | None:
        if g.config.jwt_key:  # 直接从环境中获取（适用于不存数据库的场景）
            return g.config.jwt_key
        # 建议：jwt_key进行redis缓存
        table = quoted_name("users", quote=True)
        sql = f"SELECT jwt_key FROM {table} WHERE id = :id"  # noqa
        async with g.db_async_session() as session:
            result = await session.execute(text(sql), params={"id": int(user_id)})
            row = result.fetchone()
            return row[0] if row else None


class JWTAuthorizationCredentials(HTTPAuthorizationCredentials):
    jwt_user: JWTUser


async def verify_jwt_token(token: str, token_type: str) -> JWTUser:
    try:
        # 获取
        payload = verify_jwt(token=token)
        if payload is None:
            raise CustomException(status=Status.UNAUTHORIZED_ERROR)
        user_jwt_key = await JWTUser.get_user_jwt_key(payload.get("id"))
        if not user_jwt_key:
            raise CustomException(status=Status.UNAUTHORIZED_ERROR)
        # 验证
        verify_jwt(token=token, jwt_key=user_jwt_key, token_type=token_type)
    except Exception as e:
        raise CustomException(status=Status.UNAUTHORIZED_ERROR, error=e)
    return JWTUser(**payload)


class JWTBearer(HTTPBearer):
    """从 Authorization header 获取 access_token"""

    async def __call__(self, request: Request) -> JWTAuthorizationCredentials | None:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise CustomException(
                    status=Status.UNAUTHORIZED_ERROR,
                    error="Authenticated is missing or empty",
                )
            return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise CustomException(
                    status=Status.UNAUTHORIZED_ERROR,
                    error="Invalid authentication credentials",
                )
            return None
        jwt_user = await verify_jwt_token(credentials, token_type="access")
        return JWTAuthorizationCredentials(scheme=scheme, credentials=credentials, jwt_user=jwt_user)


class JWTCookie:
    """从 Cookie 获取 refresh_token"""

    def __init__(self, cookie_name: str = _REFRESH_TOKEN_COOKIE_NAME, auto_error: bool = True):
        self.cookie_name = cookie_name
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> JWTUser | None:
        token = request.cookies.get(self.cookie_name)
        if not token:
            if self.auto_error:
                raise CustomException(
                    status=Status.UNAUTHORIZED_ERROR,
                    error="Refresh token is missing or empty",
                )
            return None
        return await verify_jwt_token(token, token_type="refresh")


async def get_current_user(
    credentials: JWTAuthorizationCredentials | None = Depends(JWTBearer(auto_error=True))
) -> JWTUser:
    """获取当前用户，用于认证 access token（从 Authorization header）"""
    if not credentials:
        return JWTUser()
    return credentials.jwt_user


async def get_current_user_from_refresh_token(
    jwt_user: JWTUser | None = Depends(JWTCookie(auto_error=True))
) -> JWTUser:
    """获取当前用户，用于认证 refresh token（从 Cookie）"""
    if not jwt_user:
        return JWTUser()
    return jwt_user


# -------------------- api key --------------------

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_api_key(
    api_key: str | None = Security(_API_KEY_HEADER)
) -> str:
    """获取当前 api key, 用于认证 api key"""
    if not api_key:
        raise CustomException(status=Status.UNAUTHORIZED_ERROR, error="API key is missing or empty")
    if api_key not in g.config.api_keys:
        raise CustomException(status=Status.UNAUTHORIZED_ERROR, error="Invalid API key")
    return api_key
