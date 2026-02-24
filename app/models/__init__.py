"""
数据模型
"""
from sqlalchemy.orm import DeclarativeBase
from toollib.sqlacrud import CRUDMixin


class DeclBase(DeclarativeBase, CRUDMixin):
    """数据模型基类

    继承`CRUDMixin`，则集成增删改查等操作，详情请查看 -> toollib.sqlacrud.CRUDMixin
    """
    pass
