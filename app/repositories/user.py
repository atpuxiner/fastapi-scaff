from app.models.user import User
from app.utils import db_util


class UserRepo:

    def __init__(self, session, model=User):
        self.session = session
        self.model = model

    async def get_user_detail(self, fields, filter_by: dict):
        return await db_util.fetch_one(self.session, self.model, fields=fields, filter_by=filter_by)

    async def get_user_lst(self, fields, page: int, size: int):
        return await db_util.fetch_all(self.session, self.model, fields=fields, page=page, size=size)

    async def get_user_total(self):
        return await db_util.fetch_total(self.session, self.model)

    async def create_user(self, data: dict, check_unique: dict = None):
        return await db_util.create(self.session, self.model, data=data, check_unique=check_unique)

    async def update_user(self, data: dict, filter_by: dict):
        return await db_util.update(self.session, self.model, data=data, filter_by=filter_by)

    async def delete_user(self, filter_by: dict):
        return await db_util.delete(self.session, self.model, filter_by=filter_by)
