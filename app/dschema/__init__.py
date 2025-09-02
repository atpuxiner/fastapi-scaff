"""
数据结构（data schema）
"""
from sqlalchemy.orm import declarative_base

DeclBase = declarative_base()


def filter_fields(
        model,
        exclude: list = None,
):
    if exclude:
        return list(set(model.model_fields.keys()) - set(exclude))
    return list(model.model_fields.keys())
