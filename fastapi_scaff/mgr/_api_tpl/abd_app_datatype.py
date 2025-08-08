from pydantic import BaseModel, Field
from sqlalchemy import Column, String

from app.datatype import DeclBase, filter_fields
from app.initializer import g


class Tpl(DeclBase):
    __tablename__ = "tpl"

    id = Column(String(20), primary_key=True, default=g.snow_cli.gen_uid, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")


class TplDetailMdl(BaseModel):
    id: str = Field(...)
    # #
    name: str = None

    @classmethod
    def response_fields(cls):
        return filter_fields(
            cls,
            exclude=[]
        )
