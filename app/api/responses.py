import json
from typing import Mapping, Any

from fastapi.encoders import jsonable_encoder
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse, StreamingResponse, ContentStream
from toollib.utils import map_jsontype

from app.api.status import Status
from app.initializer.context import request_id_var

_EXPOSE_ERROR = True


class Responses:

    @staticmethod
    def success(
        data: dict | list | str | None = None,
        msg: str = None,
        code: int = None,
        status: Status = Status.SUCCESS,
        is_encode_data: bool = False,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> JSONResponse:
        content = {
            "msg": msg or status.msg,
            "code": code or status.code,
            "data": Responses.encode_data(data) if is_encode_data else data,
            "request_id": request_id_var.get(),
        }
        return JSONResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @staticmethod
    def failure(
        msg: str = None,
        code: int = None,
        error: str | Exception | None = None,
        data: dict | list | str | None = None,
        status: Status = Status.FAILURE,
        is_encode_data: bool = False,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> JSONResponse:
        content = {
            "msg": msg or status.msg,
            "code": code or status.code,
            "data": Responses.encode_data(data) if is_encode_data else data,
            "request_id": request_id_var.get(),
        }
        if _EXPOSE_ERROR:
            content["error"] = str(error) if error else None
        return JSONResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    @staticmethod
    def encode_data(data: Any) -> Any:
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        if isinstance(data, (dict, list)):
            try:
                json.dumps(data)
                return data
            except (TypeError, OverflowError):
                pass
        return jsonable_encoder(data)

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
    data: dict = None,  # 数据(dict): key-字段，value-类型
    docs_extra: dict = None,
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
            "description": "操作成功【code为0 & http状态码200】",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "string",
                        "code": "integer",
                        "data": format_data,
                        "request_id": "string",
                    }
                }
            }
        },
        422: {
            "description": "操作失败【code非0 & http状态码200】",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "string",
                        "code": "integer",
                        "error": "string",
                        "data": "object | array | ...",
                        "request_id": "string",
                    }
                }
            }
        },
    }
    if docs_extra:
        docs.update(docs_extra)
    return docs
