from pydantic import BaseModel, Field


class TplDetail(BaseModel):
    id: str = Field(...)
    # #
    name: str = None
