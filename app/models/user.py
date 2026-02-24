import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import mapped_column

from app.models import DeclBase
from app.utils.ext_util import gen_snow_id, now_timestamp


class User(DeclBase):
    __tablename__ = "users"

    id = mapped_column(BigInteger, primary_key=True, default=gen_snow_id, nullable=False, comment="主键")
    phone = mapped_column(String(11), unique=True, index=True, nullable=False, comment="手机号")
    password = mapped_column(String(60), nullable=False, comment="密码（存储密文）")
    jwt_key = mapped_column(String(64), nullable=False, comment="jwt密钥")
    status = mapped_column(Integer, default=1, nullable=False, comment="状态：1-正常，2-禁用")
    role = mapped_column(String(10), default="user", nullable=False, comment="角色：admin，user")
    name = mapped_column(String(50), nullable=False, comment="名称")
    age = mapped_column(Integer, nullable=False, comment="年龄")
    gender = mapped_column(Integer, nullable=False, comment="性别")
    created_at = mapped_column(BigInteger, default=now_timestamp, nullable=False, comment="创建时间")
    updated_at = mapped_column(BigInteger, default=now_timestamp, onupdate=now_timestamp, nullable=False, comment="更新时间")


class UserList(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)


class UserCreate(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    password: str = Field(...)
    role: Literal["admin", "user"] | None = Field("user")
    name: str | None = Field(None, min_length=1, max_length=50)
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


class UserUpdate(BaseModel):
    name: str | None = Field(None)
    age: int | None = Field(None, ge=0, le=200)
    gender: Literal[0, 1, 2] | None = Field(None)

    @field_validator("name")
    def validate_name(cls, v):
        if v and not re.match(r"^[\u4e00-\u9fffA-Za-z0-9_\-.]{1,50}$", v):
            raise ValueError("名称仅限1-50位的中文、英文、数字、_-.组合")
        return v


class UserLogin(BaseModel):
    phone: str = Field(...)
    password: str = Field(...)
