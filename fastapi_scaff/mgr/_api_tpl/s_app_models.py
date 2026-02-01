from sqlalchemy import BigInteger, String
from sqlalchemy.orm import mapped_column

from app.models import DeclBase
from app.utils.ext_util import gen_snow_id, now_timestamp


class Tpl(DeclBase):
    __tablename__ = "tpls"

    id = mapped_column(BigInteger, primary_key=True, default=gen_snow_id, comment="主键")
    name = mapped_column(String(50), unique=True, index=True, nullable=False, comment="名称")
    # #
    created_at = mapped_column(BigInteger, default=now_timestamp, comment="创建时间")
    updated_at = mapped_column(BigInteger, default=now_timestamp, onupdate=now_timestamp, comment="更新时间")
