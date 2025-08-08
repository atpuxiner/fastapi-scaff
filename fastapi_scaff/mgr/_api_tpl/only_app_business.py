from pydantic import BaseModel, Field


class TplDetailBiz(BaseModel):
    id: str = Field(...)

    async def detail(self):
        # TODO: 业务逻辑
        pass
