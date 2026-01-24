from app.models.tpl import Tpl


class TplRepo:

    def __init__(self, session, model=Tpl):
        self.session = session
        self.model = model

    async def get_user_detail(self):
        pass
