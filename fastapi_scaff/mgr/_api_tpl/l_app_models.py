from pydantic import BaseModel, Field
from sqlalchemy import Column, String

from app.models import DeclBase, filter_fields


class Tpl(DeclBase):
    __tablename__ = "tpl"

    id = Column(String(32), primary_key=True, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")


class TplDetail(BaseModel):
    id: str = Field(...)
    # #
    name: str = None

    @classmethod
    def response_fields(cls):
        return filter_fields(
            cls,
            exclude=[]
        )
