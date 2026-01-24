from app.schemas.tpl import (
    TplDetail,
)


class TplDetailSvc(TplDetail):
    model_config = {
        "json_schema_extra": {
            "title": "TplDetail"
        }
    }

    async def detail(self):
        # TODO: 业务逻辑
        pass
