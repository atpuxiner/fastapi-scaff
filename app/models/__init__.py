"""
数据模型
"""
from sqlalchemy.orm import DeclarativeBase


class DeclBase(DeclarativeBase):
    pass


# DeclBase 使用示例（官方文档：https://docs.sqlalchemy.org/en/latest/orm/quickstart.html#declare-models）
"""
from sqlalchemy import Column, String

from app.services import DeclBase


class User(DeclBase):
    __tablename__ = "user"

    id = Column(String(20), primary_key=True, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")
"""
