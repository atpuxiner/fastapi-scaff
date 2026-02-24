from pydantic import BaseModel, Field


class Tpl:
    __tablename__ = "tpls"


class TplList(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)
