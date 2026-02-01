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
        if data is None or isinstance(data, (str, int, float, bool)):
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
        model=None,  # 模型(BaseModel): 自动从模型获取response_fields
        data: dict | str = None,  # 数据(dict/str): 直接给定字段与类型/类型
        is_listwrap: bool = False,
        listwrap_key: str = None,
        listwrap_key_extra: dict = None,
        docs_extra: dict = None,
):
    """响应文档"""

    def _data_from_model(model_, default: str = "N/A") -> dict:
        """数据模板"""
        data_ = {}
        if hasattr(model_, "response_fields"):
            for field_name in model_.response_fields() or []:
                data_[field_name] = default
        return data_

    final_data = {}
    if model:
        final_data = _data_from_model(model)
    if data:
        if isinstance(data, dict):
            final_data.update(data)
        else:
            final_data = data
    if is_listwrap:
        final_data = [final_data] if not isinstance(final_data, list) else final_data
        if listwrap_key:
            final_data = {listwrap_key: final_data}
            if listwrap_key_extra:
                final_data.update(listwrap_key_extra)

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

    format_data = _format_value(final_data)

    docs = {
        200: {
            "description": "操作成功【code为0 & http状态码200】",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "string",
                        "code": "integer",
                        "data": format_data or "object | array | ...",
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
