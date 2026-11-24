"""应用单元测试：不启动 HTTP 服务，直接覆盖核心工具、模型校验、认证依赖与服务层。"""

import asyncio
import importlib
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response

import app.core._db as db_module
from app.core import g
from app.core._conf import init_config
from app.core._redis import init_redis_cli
from app.core._db import create_tables, import_tables, make_db_url
from app.core._snow import _snow_incr, init_snow_cli
from app.core.context import client_ip_var, request_id_var
from app.core.exceptions import CustomException
from app.core.middleware import (
    ExceptionsHandler,
    HttpMiddleware,
    _format_validation_error,
    _is_sensitive,
    _mask_data,
)
from app.core.responses import Responses, response_docs
from app.core.status import Status
from app.models.user import User, UserCreate, UserList, UserLogin, UserUpdate
from app.services.user import UserSvc, get_user_svc
from app.utils.cookie_util import clear_refresh_token_cookie, set_refresh_token_cookie
from app.utils.ext_util import gen_snow_id, gen_uuid_hex, now_timestamp
from app.utils.jwt_util import gen_jwt, verify_jwt
from app.api import deps


class FakeDbSession:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


@asynccontextmanager
async def fake_db_session(session):
    yield session


def patch_db_session(monkeypatch, session=None):
    session = session or FakeDbSession()
    # cached_property 在实例上尚未生成；raising=False 避免 getattr 触发真实初始化。
    monkeypatch.setattr(g, "db_async_session", lambda: fake_db_session(session), raising=False)
    return session


def test_custom_exception_attributes():
    exc = CustomException(status=Status.NOT_FOUND_ERROR, msg="missing", error="detail", data={"id": "1"})
    assert exc.status is Status.NOT_FOUND_ERROR
    assert exc.msg == "missing"
    assert exc.code == Status.NOT_FOUND_ERROR.code
    assert str(exc) == f"{exc.code}: missing"
    assert "CustomException" in repr(exc)
    assert CustomException().msg == Status.FAILURE.msg


def test_response_docs_and_stream():
    docs = response_docs(data={"id": "str"}, docs_extra={418: {"description": "teapot"}})
    assert {200, 400, 401, 403, 404, 422, 500, 418} <= set(docs)
    assert docs[200]["content"]["application/json"]["example"]["data"] == {"id": "string"}
    assert docs[418]["description"] == "teapot"

    stream = Responses.stream(iter([b"a"]), media_type="text/plain")
    assert stream.status_code == 200
    assert stream.media_type == "text/plain"
    assert hasattr(stream.body_iterator, "__aiter__")


def test_context_vars_have_defaults_and_can_be_reset():
    token = request_id_var.set("rid")
    assert request_id_var.get() == "rid"
    assert client_ip_var.get() == "-"
    request_id_var.reset(token)
    assert request_id_var.get() == "-"


def test_middleware_helpers():
    assert _is_sensitive("user_password")
    assert not _is_sensitive("nickname")
    assert _mask_data({"password": "x", "nested": {"api_key": "y"}, "name": "z"}) == {
        "password": "***",
        "nested": {"api_key": "***"},
        "name": "z",
    }
    assert "phone (string) too short".lower() == _format_validation_error(
        {"loc": ("body", "phone"), "type": "string", "msg": "too short"}
    )


def test_request_id_and_client_ip_helpers():
    valid = SimpleNamespace(headers={"X-Request-ID": "abc-1"})
    assert HttpMiddleware._get_or_create_request_id(valid) == "abc-1"

    invalid = SimpleNamespace(headers={"X-Request-ID": "bad id!"})
    generated = HttpMiddleware._get_or_create_request_id(invalid)
    assert generated != "bad id!" and len(generated) == 36

    request = SimpleNamespace(
        headers={"X-Forwarded-For": "bad, 1.2.3.4, 5.6.7.8", "X-Real-IP": "9.9.9.9"},
        client=SimpleNamespace(host="10.0.0.1"),
    )
    assert HttpMiddleware._get_client_ip(request) == "1.2.3.4"
    request.headers = {"X-Real-IP": "not-an-ip"}
    assert HttpMiddleware._get_client_ip(request) == "10.0.0.1"


def test_http_exception_handler_uses_status_mapping():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/missing",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
        }
    )
    response = asyncio.run(
        ExceptionsHandler.http_exception_handler(
            request,
            SimpleNamespace(status_code=404, detail="gone", headers=None),
        )
    )
    assert response.status_code == 404
    assert b'"code":404' in response.body
    assert b'"msg":"gone"' in response.body


def test_jwt_expiry_and_unverified_decode():
    token = gen_jwt({"id": "1"}, "s" * 32, typ="refresh", exp_seconds=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_jwt(token, key="s" * 32)
    assert verify_jwt(token)["typ"] == "refresh"


def test_cookie_helpers():
    response = Response()
    set_refresh_token_cookie(response, "rt", 100, secure=True)
    cookie = response.headers["set-cookie"]
    assert "x_refresh_token=rt" in cookie
    assert "Max-Age=100" in cookie
    assert "Path=/api" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie

    cleared = Response()
    clear_refresh_token_cookie(cleared)
    assert "Max-Age=0" in cleared.headers["set-cookie"]


def test_id_and_timestamp_utils(monkeypatch):
    assert len(gen_uuid_hex()) == 32
    assert isinstance(now_timestamp(), int)
    monkeypatch.setattr(g, "snow_cli", SimpleNamespace(gen_uid=lambda to_str=False: "123"), raising=False)
    assert gen_snow_id(to_str=True) == "123"


@pytest.mark.parametrize("relative", [False, True])
def test_make_db_url_resolves_sqlite_path(tmp_path, monkeypatch, relative):
    if relative:
        monkeypatch.setattr(db_module, "APP_DIR", tmp_path / "app")
        database = "data/db/relative.sqlite3"
        expected = tmp_path / "data/db/relative.sqlite3"
    else:
        database = str(tmp_path / "absolute.sqlite3")
        expected = tmp_path / "absolute.sqlite3"
    url = make_db_url("sqlite+aiosqlite", database)
    assert url.drivername == "sqlite+aiosqlite"
    assert url.database == str(expected.resolve())


def test_import_tables_registers_user_table():
    decl_base = import_tables()
    assert decl_base is not None
    assert "users" in decl_base.metadata.tables


def test_create_tables_writes_sqlite_schema(tmp_path):
    db_file = tmp_path / "schema.sqlite3"
    create_tables("sqlite", str(db_file), None, None, None, None, None)
    with sqlite3.connect(db_file) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "users" in tables


def test_redis_initializer_forwards_options(monkeypatch):
    sentinel = object()
    captured = {}

    def fake_redis_cli(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr("app.core._redis.RedisCli", fake_redis_cli)
    result = init_redis_cli(host="127.0.0.1", port=6379, db=2, password="pw", max_connections=5)
    assert result is sentinel
    assert captured == {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 2,
        "password": "pw",
        "max_connections": 5,
    }


def test_snowflake_initializers_with_stub_redis():
    class FakeRedis:
        @contextmanager
        def connection(self):
            yield SimpleNamespace(ping=lambda: True, eval=lambda *args: 3)

    fake = FakeRedis()
    assert _snow_incr(fake, "key", 60) == 3
    assert _snow_incr(None, "key", 60) is None
    assert init_snow_cli(redis_cli=fake, datacenter_id=5) is not None


def test_config_reads_environment(monkeypatch, tmp_path):
    db_path = str(tmp_path / "config.sqlite3")
    env = {
        "APP_TITLE": "Unit App",
        "APP_DEBUG": "false",
        "API_KEYS": '["key-one", "key-two"]',
        "DB_DRIVERNAME": "sqlite",
        "DB_ASYNC_DRIVERNAME": "sqlite+aiosqlite",
        "DB_DATABASE": db_path,
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
    }
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    config = init_config()
    assert config.APP_TITLE == "Unit App"
    assert config.APP_DEBUG is False
    assert config.API_KEYS == ["key-one", "key-two"]
    assert db_path == config.DB_DATABASE
    assert config.REDIS_PORT == 6379


def test_user_model_validators():
    created = UserCreate(phone="13800138000", password="abc12345")
    assert created.nickname is None
    assert created.role == "user" and created.age == 18 and created.gender == 0
    assert UserCreate(phone="13800138000", password="abc12345", nickname="Tom_123").nickname == "Tom_123"

    with pytest.raises(ValidationError):
        UserCreate(phone="13800138000", password="short1")
    with pytest.raises(ValidationError):
        UserCreate(phone="13800138000", password="abc12345", role="root")
    with pytest.raises(ValidationError):
        UserCreate(phone="13800138000", password="abc12345", nickname="bad name!")
    with pytest.raises(ValidationError):
        UserUpdate(nickname="bad name!")
    assert UserList().size == 10
    with pytest.raises(ValidationError):
        UserList(size=201)


def test_get_user_service_is_cached():
    assert get_user_svc() is get_user_svc()
    assert isinstance(get_user_svc(), UserSvc)


def test_user_service_list_user(monkeypatch):
    patch_db_session(monkeypatch)
    fetch_all = AsyncMock(return_value=[{"id": "1"}])
    count = AsyncMock(return_value=2)
    monkeypatch.setattr(User, "fetch_all", fetch_all)
    monkeypatch.setattr(User, "count", count)

    result = asyncio.run(UserSvc.list_user(UserList(page=2, size=5, phone="138")))
    assert result == {"items": [{"id": "1"}], "total": 2}
    kwargs = fetch_all.await_args.kwargs
    assert (kwargs["offset"], kwargs["limit"]) == (5, 5)
    assert len(kwargs["where"]) == 1
    assert kwargs["converters"] == {"id": str}
    count.assert_awaited_once()


def test_user_service_create_user_and_conflict(monkeypatch):
    session = patch_db_session(monkeypatch)
    monkeypatch.setattr(g.config, "JWT_KEY", "", raising=False)
    from app.utils.jwt_util import verify_password

    create = AsyncMock(return_value=SimpleNamespace(data={"id": 7}))
    monkeypatch.setattr(User, "create", create)
    result = asyncio.run(UserSvc.create_user(UserCreate(phone="13800138000", password="abc12345")))
    assert result == {"id": "7"}
    assert verify_password("abc12345", create.await_args.kwargs["values"]["password"])
    assert create.await_args.kwargs["on_conflict"] == {"phone": "13800138000"}
    assert session.commits == 1

    monkeypatch.setattr(User, "create", AsyncMock(return_value=None))
    with pytest.raises(CustomException) as exc:
        asyncio.run(UserSvc.create_user(UserCreate(phone="13800138000", password="abc12345")))
    assert exc.value.status is Status.RECORD_EXISTS_ERROR


def test_user_service_get_and_delete_user_errors(monkeypatch):
    patch_db_session(monkeypatch)
    monkeypatch.setattr(User, "fetch_one", AsyncMock(return_value=None))
    with pytest.raises(CustomException) as exc:
        asyncio.run(UserSvc.get_user("42"))
    assert exc.value.status is Status.RECORD_NOT_EXIST_ERROR

    monkeypatch.setattr(User, "delete", AsyncMock(return_value=None))
    with pytest.raises(CustomException) as exc:
        asyncio.run(UserSvc.delete_user("42"))
    assert exc.value.status is Status.RECORD_NOT_EXIST_ERROR


def test_user_service_login_refresh_logout(monkeypatch):
    from app.utils.jwt_util import hash_password

    session = patch_db_session(monkeypatch)
    monkeypatch.setattr(g.config, "JWT_KEY", "unit-test-signing-key-000000000000", raising=False)
    user_row = {
        "id": "7",
        "phone": "13800138000",
        "status": 1,
        "role": "user",
        "nickname": "tester",
        "avatar": None,
        "password": hash_password("abc12345"),
    }
    monkeypatch.setattr(User, "fetch_one", AsyncMock(return_value=user_row.copy()))
    update = AsyncMock(return_value=1)
    monkeypatch.setattr(User, "update", update)

    login = asyncio.run(UserSvc.auth_login(UserLogin(phone="13800138000", password="abc12345")))
    assert login["expires_in"] == 7200
    assert login["refresh_expires_in"] == 2592000
    assert "password" not in login["user_info"]
    assert verify_jwt(login["access_token"], key="unit-test-signing-key-000000000000", typ="access")["id"] == "7"
    assert verify_jwt(login["refresh_token"], key="unit-test-signing-key-000000000000", typ="refresh")["id"] == "7"
    assert session.commits == 1

    refreshed = asyncio.run(UserSvc.auth_refresh("7"))
    assert verify_jwt(refreshed["access_token"], key="unit-test-signing-key-000000000000", typ="access")["id"] == "7"
    assert "user_info" not in refreshed

    logged_out = asyncio.run(UserSvc.auth_logout("7"))
    assert logged_out == {"id": "7"}


def test_user_service_rejects_disabled_user(monkeypatch):
    from app.utils.jwt_util import hash_password

    patch_db_session(monkeypatch)
    monkeypatch.setattr(
        User,
        "fetch_one",
        AsyncMock(return_value={"id": "7", "status": 2, "password": hash_password("abc12345")}),
    )
    with pytest.raises(CustomException) as exc:
        asyncio.run(UserSvc.auth_login(UserLogin(phone="13800138000", password="abc12345")))
    assert exc.value.status is Status.USER_ABNORMAL_ERROR


def test_jwt_user_key_from_config(monkeypatch):
    monkeypatch.setattr(g.config, "JWT_KEY", "cfg-key", raising=False)
    assert asyncio.run(deps.JWTUser.get_user_jwt_key("1")) == "cfg-key"


def test_verify_jwt_token_wraps_failures(monkeypatch):
    monkeypatch.setattr(deps, "verify_jwt", lambda **kwargs: {"id": "1"})
    monkeypatch.setattr(deps.JWTUser, "get_user_jwt_key", AsyncMock(return_value=None))
    with pytest.raises(CustomException) as exc:
        asyncio.run(deps.verify_jwt_token("token", "access"))
    assert exc.value.status is Status.UNAUTHORIZED_ERROR

    monkeypatch.setattr(deps.JWTUser, "get_user_jwt_key", AsyncMock(return_value="key"))
    user = asyncio.run(deps.verify_jwt_token("token", "access"))
    assert user.id == "1"


def test_jwt_bearer_and_cookie_dependencies(monkeypatch):
    request = SimpleNamespace(headers={})
    with pytest.raises(CustomException) as exc:
        asyncio.run(deps.JWTBearer(auto_error=True)(request))
    assert exc.value.code == Status.UNAUTHORIZED_ERROR.code

    request.headers = {"Authorization": "Basic abc"}
    with pytest.raises(CustomException):
        asyncio.run(deps.JWTBearer(auto_error=True)(request))

    request.headers = {"Authorization": "Bearer abc"}
    monkeypatch.setattr(deps, "verify_jwt_token", AsyncMock(return_value=deps.JWTUser(id="1")))
    credentials = asyncio.run(deps.JWTBearer(auto_error=True)(request))
    assert credentials.scheme == "Bearer"
    assert credentials.jwt_user.id == "1"

    cookie_request = SimpleNamespace(cookies={})
    with pytest.raises(CustomException):
        asyncio.run(deps.JWTCookie()(cookie_request))
    assert asyncio.run(deps.JWTCookie(auto_error=False)(cookie_request)) is None
    cookie_request.cookies = {"x_refresh_token": "refresh-token"}
    user = asyncio.run(deps.JWTCookie()(cookie_request))
    assert user.id == "1"


def test_api_key_dependency(monkeypatch):
    monkeypatch.setattr(g.config, "API_KEYS", ["valid-key"], raising=False)
    assert asyncio.run(deps.get_current_api_key("valid-key")) == "valid-key"
    with pytest.raises(CustomException) as exc:
        asyncio.run(deps.get_current_api_key("bad"))
    assert exc.value.status is Status.UNAUTHORIZED_ERROR
    with pytest.raises(CustomException):
        asyncio.run(deps.get_current_api_key(None))


def test_app_disables_docs_when_configured(isolated_app, monkeypatch):
    import app.core as core

    main_module = importlib.import_module("app.main")
    monkeypatch.setattr(core.g.config, "APP_DISABLE_DOCS", True)
    try:
        disabled = importlib.reload(main_module)
        assert disabled.openapi_url is None
        assert disabled.docs_url is None
        assert disabled.redoc_url is None
    finally:
        monkeypatch.setattr(core.g.config, "APP_DISABLE_DOCS", False)
        importlib.reload(main_module)
