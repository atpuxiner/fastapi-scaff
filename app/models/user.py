from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import mapped_column

from app.models import DeclBase
from app.utils.ext_util import gen_snow_id, now_timestamp


class User(DeclBase):
    __tablename__ = "users"

    id = mapped_column(BigInteger, primary_key=True, default=gen_snow_id, comment="主键")
    phone = mapped_column(String(11), unique=True, index=True, nullable=False, comment="手机号")
    password = mapped_column(String(60), nullable=False, comment="密码（存储密文）")
    jwt_key = mapped_column(String(64), nullable=True, comment="jwt密钥")
    status = mapped_column(Integer, default=1, nullable=True, comment="状态：1-正常，2-禁用")
    role = mapped_column(String(10), default="user", nullable=True, comment="角色：admin，user")
    name = mapped_column(String(50), nullable=True, comment="名称")
    age = mapped_column(Integer, nullable=True, comment="年龄")
    gender = mapped_column(Integer, nullable=True, comment="性别")
    created_at = mapped_column(BigInteger, default=now_timestamp, comment="创建时间")
    updated_at = mapped_column(BigInteger, default=now_timestamp, onupdate=now_timestamp, comment="更新时间")
