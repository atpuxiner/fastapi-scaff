from pydantic import BaseModel


class TplDetailSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplDetail"
        }
    }

    async def detail(self):
        # TODO: 业务逻辑
        pass
