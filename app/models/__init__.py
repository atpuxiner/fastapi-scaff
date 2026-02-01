"""
数据模型
"""
from sqlalchemy.orm import DeclarativeBase
from toollib.sqlacrud import CRUDMixin


class DeclBase(DeclarativeBase, CRUDMixin):
    """数据模型基类

    CRUDMixin 使模型类自带异步 CRUD 操作方法，无需显式传递 model 参数

    e.g.::

        from sqlalchemy import BigInteger, String
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
        from toollib.sqlacrud import CRUDMixin

        class DeclBase(DeclarativeBase, CRUDMixin):
            pass


        class User(DeclBase):
            __tablename__ = "users"

            id = mapped_column(BigInteger, primary_key=True, comment="主键")
            name = mapped_column(String(50), nullable=True, comment="名称")


        # 使用
        async def example(session: AsyncSession):
            # 查询
            user = await User.fetch_one(session, where={"id": 1})
            users = await User.fetch_all(session, limit=10)

            # 创建
            created = await User.create(session, values={"name": "Tom"})

            # 删除
            deleted = await User.delete(session, where={"id": 1})

            # 更新
            updated = await User.update(session, values={"name": "New"}, where={"id": 1})

            # ...

    """
    pass
