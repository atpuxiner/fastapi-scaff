from functools import lru_cache


class TplSvc:
    @staticmethod
    async def list_tpl(req):
        # TODO: 业务逻辑
        result = []
        total = 0
        return {"items": result, "total": total}


@lru_cache(maxsize=128)
def get_tpl_svc() -> TplSvc:
    return TplSvc()
