from pydantic import BaseModel, Field

from app.schemas import filter_fields


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
