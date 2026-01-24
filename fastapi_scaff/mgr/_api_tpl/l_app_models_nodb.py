from pydantic import BaseModel, Field


class Tpl:  # 请根据自身需求修改
    __tablename__ = "tpl"


class TplDetail(BaseModel):
    id: str = Field(...)
    # #
    name: str = None
