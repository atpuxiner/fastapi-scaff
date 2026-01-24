from sqlalchemy import Column, String

from app.models import DeclBase


class Tpl(DeclBase):
    __tablename__ = "tpl"

    id = Column(String(20), primary_key=True, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")
