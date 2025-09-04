import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schema import filter_fields


class UserDetail(BaseModel):
    id: str = Field(...)
    # #
    phone: str = None
    name: str = None
    age: int = None
    gender: int = None
    created_at: int = None
    updated_at: int = None

    @classmethod
    def response_fields(cls):
        return filter_fields(
            cls,
            exclude=[]
        )


class UserList(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1)
    # #
    id: str = None
    phone: str = None
    name: str = None
    age: int = None
    gender: int = None
    created_at: int = None
    updated_at: int = None

    @classmethod
    def response_fields(cls):
        return filter_fields(
            cls,
            exclude=[
                "page",
                "size",
            ]
        )


class UserCreate(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    password: str = Field(...)
    name: str | None = Field(None)
    age: int | None = Field(None, ge=0, le=200)
    gender: Literal[1, 2] | None = Field(None)

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


class UserUpdate(BaseModel):
    name: str | None = Field(None)
    age: int | None = Field(None, ge=0, le=200)
    gender: Literal[1, 2] | None = Field(None)

    @field_validator("name")
    def validate_name(cls, v):
        if v and not re.match(r"^[\u4e00-\u9fffA-Za-z0-9_\-.]{1,50}$", v):
            raise ValueError("名称仅限1-50位的中文、英文、数字、_-.组合")
        return v


class UserDelete(BaseModel):
    pass


class UserLogin(BaseModel):
    phone: str = Field(...)
    password: str = Field(...)


class UserToken(BaseModel):
    id: str = Field(...)
    exp_minutes: int = Field(24 * 60 * 30, ge=1)
