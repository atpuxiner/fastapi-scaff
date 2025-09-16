from sqlalchemy import Column, String

from app.models import DeclBase
from app.initializer import g


class Tpl(DeclBase):
    __tablename__ = "tpl"

    id = Column(String(20), primary_key=True, default=g.snow_cli.gen_uid, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")
