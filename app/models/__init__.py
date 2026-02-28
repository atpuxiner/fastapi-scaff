"""
数据模型
"""
from sqlalchemy.orm import DeclarativeBase
from toollib.sqlacrud import CRUDMixin


class DeclBase(DeclarativeBase, CRUDMixin):
    """数据模型基类，集成 CRUD 操作"""
