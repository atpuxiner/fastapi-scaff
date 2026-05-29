from collections.abc import Mapping

from fastapi.encoders import jsonable_encoder
from starlette.background import BackgroundTask
from starlette.responses import ContentStream, JSONResponse, StreamingResponse
from toollib.utils import map_jsontype

from app.core.context import request_id_var
from app.core.status import Status

_EXPOSE_ERROR = True


class Responses:
    @staticmethod
    def success(
        data: dict | list | str | None = None,
        msg: str | None = None,
        code: int | None = None,
        status: Status = Status.SUCCESS,
        encode_data: bool = False,
        status_code: int | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> JSONResponse:
        content = {
            "msg": msg or status.msg,
            "code": code or status.code,
            "data": jsonable_encoder(data) if encode_data else data,
            "request_id": request_id_var.get(),
        }
        return JSONResponse(
            content=content,
            status_code=status_code or status.status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @staticmethod
    def failure(
        status: Status = Status.FAILURE,
        msg: str | None = None,
        code: int | None = None,
        error: str | Exception | None = None,
        data: dict | list | str | None = None,
        encode_data: bool = False,
        status_code: int | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> JSONResponse:
        content = {
            "msg": msg or status.msg,
            "code": code or status.code,
            "data": jsonable_encoder(data) if encode_data else data,
            "request_id": request_id_var.get(),
        }
        if _EXPOSE_ERROR:
            content["error"] = str(error) if error else None
        return JSONResponse(
            content=content,
            status_code=status_code or status.status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @staticmethod
    def stream(
        content: ContentStream,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> StreamingResponse:
        return StreamingResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


def response_docs(
    data: dict | None = None,  # data文档（key=字段名，value=字段类型或示例）
    docs_extra: dict | None = None,
):
    """响应文档"""

    def _format_value(value):
        if isinstance(value, str):
            _value = value.split("|")
            if len(_value) > 1:
                return " | ".join([map_jsontype(_v.strip(), is_keep_integer=True) for _v in _value])
            return map_jsontype(value, is_keep_integer=True)
        elif isinstance(value, dict):
            return {k: _format_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [_format_value(item) for item in value]
        else:
            return str(value)

    format_data = _format_value(data) if data else "object | array | ..."

    docs = {
        200: {
            "description": "✅ 操作成功",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "操作成功",
                        "code": 0,
                        "data": format_data,
                        "request_id": "string",
                    }
                }
            },
        },
        400: {
            "description": "❌ 参数错误/业务失败",
            "content": {
                "application/json": {
                    "example": {"msg": "参数错误/业务失败", "code": 400, "error": "string", "data": None, "request_id": "string"}
                }
            },
        },
        401: {
            "description": "🔒 认证失败",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "认证失败，请先登录",
                        "code": 401,
                        "error": None,
                        "data": None,
                        "request_id": "string",
                    }
                }
            },
        },
        403: {
            "description": "🚫 禁止访问",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "权限不足，无法访问",
                        "code": 403,
                        "error": None,
                        "data": None,
                        "request_id": "string",
                    }
                }
            },
        },
        404: {
            "description": "🔍 资源未找到",
            "content": {
                "application/json": {
                    "example": {"msg": "资源未找到", "code": 404, "error": None, "data": None, "request_id": "string"}
                }
            },
        },
        422: {
            "description": "⚠️ 数据校验失败",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "数据校验失败",
                        "code": 422,
                        "error": "string",
                        "data": None,
                        "request_id": "string",
                    }
                }
            },
        },
        500: {
            "description": "🔥 服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "服务开小差了，请稍后再试",
                        "code": 500,
                        "error": "string",
                        "data": None,
                        "request_id": "string",
                    }
                }
            },
        },
    }
    if docs_extra:
        docs.update(docs_extra)
    return docs
