from app.models.tpl import Tpl
from app.utils import db_util


class TplRepo:

    def __init__(self, session, model=Tpl):
        self.session = session
        self.model = model

    async def get_user_detail(self, fields, filter_by: dict):
        return await db_util.fetch_one(self.session, self.model, fields=fields, filter_by=filter_by)
