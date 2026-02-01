from pydantic import BaseModel, Field


class TplListSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplList"
        }
    }
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)

    async def list_tpl(self):
        # TODO: 业务逻辑
        pass
