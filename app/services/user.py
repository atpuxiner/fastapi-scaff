import re
from typing import Literal

from pydantic import Field, BaseModel, field_validator

from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.models.user import User
from app.utils import jwt_util


class UserListSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserList"
        }
    }
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)

    async def list_user(self):
        async with g.db_async_session() as session:
            data = await User.fetch_all(
                session=session,
                columns=self.response_fields(),
                offset=(self.page - 1) * self.size,
                limit=self.size,
            )
            total = await User.count(session=session)
            return data, total

    @staticmethod
    def response_fields():
        return (
            "id",
            "phone",
            "status",
            "role",
            "name",
            "age",
            "gender",
            "created_at",
            "updated_at",
        )


class UserCreateSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserCreate"
        }
    }
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    password: str = Field(...)
    role: Literal["admin", "user"] | None = Field("user")
    name: str | None = Field(min_length=1, max_length=50)
    age: int | None = Field(18, ge=0, le=200)
    gender: Literal[0, 1, 2] | None = Field(0)

    @field_validator("password")
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)\S{6,20}$", v):
            raise ValueError("密码必须包含至少一个字母和一个数字，长度为6-20位的非空白字符组合")
        return v

    @field_validator("name")
    def validate_name(cls, v, info):
        if not v and (phone := info.data.get("phone")):
            return f"用户{phone[-4:]}"
        if v and not re.match(r"^[\u4e00-\u9fffA-Za-z0-9_\-.]{1,50}$", v):
            raise ValueError("名称仅限1-50位的中文、英文、数字、_-.组合")
        return v

    async def create_user(self):
        async with g.db_async_session() as session:
            result = await User.create(
                session=session,
                values={
                    "phone": self.phone,
                    "password": jwt_util.hash_password(self.password),
                    "jwt_key": jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key),
                    "role": self.role,
                    "name": self.name,
                    "age": self.age,
                    "gender": self.gender,
                },
                on_conflict={"phone": self.phone},
                flush=True,
            )
            if not result:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            await session.commit()
            return result.data["id"]


class UserGetSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserGet"
        }
    }
    user_id: int = Field(...)

    async def get_user(self):
        async with g.db_async_session() as session:
            data = await User.fetch_one(
                session=session,
                where={"id": self.user_id},
                columns=self.response_fields(),
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            return data

    @staticmethod
    def response_fields():
        return (
            "id",
            "phone",
            "status",
            "role",
            "name",
            "age",
            "gender",
            "created_at",
            "updated_at",
        )


class UserDeleteSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserDelete"
        }
    }
    user_id: int = Field(...)

    async def delete_user(self):
        async with g.db_async_session() as session:
            result = await User.delete(
                session=session,
                where={"id": self.user_id},
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return self.user_id


class UserUpdateSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserUpdate"
        }
    }
    name: str | None = Field(None)
    age: int | None = Field(None, ge=0, le=200)
    gender: Literal[0, 1, 2] | None = Field(None)

    @field_validator("name")
    def validate_name(cls, v):
        if v and not re.match(r"^[\u4e00-\u9fffA-Za-z0-9_\-.]{1,50}$", v):
            raise ValueError("名称仅限1-50位的中文、英文、数字、_-.组合")
        return v

    async def update_user(self, user_id: int):
        async with g.db_async_session() as session:
            result = await User.update(
                session=session,
                where={"id": user_id},
                values=self.model_dump(),
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return user_id


class UserLoginSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserLogin"
        }
    }
    phone: str = Field(...)
    password: str = Field(...)

    async def login(self):
        async with g.db_async_session() as session:
            data = await User.fetch_one(
                session=session,
                where={"phone": self.phone},
                columns=(
                    "id",
                    "phone",
                    "name",
                    "status",
                    "role",
                    "age",
                    "gender",
                    "password",
                ),
            )
            if not data:
                raise CustomException(status=Status.USER_OR_PASSWORD_ERROR)
            if data.get("status", 1) != 1:
                raise CustomException(status=Status.USER_ABNORMAL_ERROR)
            stored_password = data["password"]
            payload = {
                "id": data.get("id"),
                "phone": data.get("phone"),
                "status": data.get("status"),
                "role": data.get("role"),
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
            }

        if not jwt_util.verify_password(self.password, stored_password):
            raise CustomException(status=Status.USER_OR_PASSWORD_ERROR)
        new_jwt_key = jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key)
        token = jwt_util.gen_jwt(
            payload=payload.copy(),
            jwt_key=new_jwt_key,
            exp_minutes=24 * 60 * 30,
        )
        async with g.db_async_session() as session:
            await User.update(
                session=session,
                where={"id": payload["id"]},
                values={"jwt_key": new_jwt_key},
            )
            await session.commit()

        return {"token": token, "user": payload}


class UserLogoutSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserLogout"
        }
    }
    user_id: int = Field(...)

    async def logout(self):
        new_jwt_key = jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key)
        async with g.db_async_session() as session:
            result = await User.update(
                session=session,
                where={"id": self.user_id},
                values={"jwt_key": new_jwt_key},
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
        return {"id": self.user_id}


class UserTokenSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "UserToken"
        }
    }
    user_id: int = Field(...)
    exp_minutes: int = Field(24 * 60 * 30, ge=1)

    async def token(self):
        async with g.db_async_session() as session:
            data = await User.fetch_one(
                session=session,
                where={"id": self.user_id},
                columns=("id", "phone", "name", "age", "gender", "status", "role"),
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            if data.get("status", 1) != 1:
                raise CustomException(status=Status.USER_ABNORMAL_ERROR)
            payload = {
                "id": data.get("id"),
                "phone": data.get("phone"),
                "status": data.get("status"),
                "role": data.get("role"),
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
            }

        new_jwt_key = jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key)
        token = jwt_util.gen_jwt(
            payload=payload.copy(),
            jwt_key=new_jwt_key,
            exp_minutes=self.exp_minutes,
        )
        async with g.db_async_session() as session:
            await User.update(
                session=session,
                where={"id": self.id},
                values={"jwt_key": new_jwt_key},
            )
            await session.commit()

        return token
