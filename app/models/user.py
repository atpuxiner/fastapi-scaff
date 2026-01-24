from sqlalchemy import Column, BigInteger, Integer, String

from app.initializer import g
from app.models import DeclBase
from app.utils.ext_util import now_timestamp


class User(DeclBase):
    __tablename__ = "user"

    id = Column(String(20), primary_key=True, default=g.snow_cli.gen_uid, comment="主键")
    phone = Column(String(15), unique=True, index=True, nullable=False, comment="手机号")
    password = Column(String(128), nullable=True, comment="密码")
    jwt_key = Column(String(128), nullable=True, comment="jwtKey")
    name = Column(String(50), nullable=True, comment="名称")
    age = Column(Integer, nullable=True, comment="年龄")
    gender = Column(Integer, nullable=True, comment="性别")
    created_at = Column(BigInteger, default=now_timestamp, comment="创建时间")
    updated_at = Column(BigInteger, default=now_timestamp, onupdate=now_timestamp, comment="更新时间")
