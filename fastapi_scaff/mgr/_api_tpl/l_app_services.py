from pydantic import BaseModel, Field


class TplList(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)


class TplSvc:

    @staticmethod
    async def list_tpl(req):
        # TODO: 业务逻辑
        result = []
        total = 0
        return {"items": result, "total": total}
