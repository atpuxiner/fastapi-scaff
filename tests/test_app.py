"""应用接口测试：路由注册、健康检查、用户 CRUD/认证、统一响应与异常处理。"""

import importlib
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.core import g
from app.core.exceptions import CustomException
from app.core.middleware import CorsMiddleware
from app.core.status import Status


def make_fake_user_service(**results):
    return SimpleNamespace(**{name: AsyncMock(return_value=value) for name, value in results.items()})


def override_user_service(client, **results):
    svc = make_fake_user_service(**results)
    module = importlib.import_module("app.services.user")
    client.app.dependency_overrides[module.get_user_svc] = lambda: svc
    return svc


def override_current_user(client, role="admin", user_id="7"):
    deps = importlib.import_module("app.api.deps")
    client.app.dependency_overrides[deps.get_current_user] = lambda: deps.JWTUser(id=user_id, role=role)


def override_refresh_user(client, user_id="7"):
    deps = importlib.import_module("app.api.deps")
    client.app.dependency_overrides[deps.get_current_user_from_refresh] = lambda: deps.JWTUser(id=user_id)


def test_app_metadata_and_route_registration(client):
    assert client.app.title == g.config.APP_TITLE
    assert client.app.version == g.config.APP_VERSION
    assert client.app.docs_url == "/docs"
    assert client.app.openapi_url == "/openapi.json"

    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    for path in (
        "/health",
        "/ahealth",
        "/api/v1/users",
        "/api/v1/users/{user_id}",
        "/api/v1/users/auth/login",
        "/api/v1/users/auth/logout",
        "/api/v1/users/auth/refresh",
    ):
        assert path in paths


def test_health_returns_raw_payload_and_request_id(client):
    resp = client.get("/health", headers={"X-Request-ID": "req-health-001"})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "req-health-001"
    body = resp.json()
    assert {"status", "version", "timestamp"} <= set(body)
    assert body["status"] == "ok"
    assert body["version"] == g.config.APP_VERSION
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None


def test_health_generates_valid_request_id_when_header_invalid(client):
    resp = client.get("/health", headers={"X-Request-ID": "bad id!"})
    assert resp.status_code == 200
    request_id = resp.headers["X-Request-ID"]
    assert request_id and request_id != "bad id!"


def test_ahealth_returns_published_task_id(monkeypatch, client):
    producer = importlib.import_module("celery_app.producer")
    monkeypatch.setattr(producer.publisher, "publish", lambda *args, **kwargs: "task-123")

    resp = client.get("/ahealth")
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == "task-123"
    assert body["status"] == "ok"
    assert body["version"] == g.config.APP_VERSION
    assert "request_id" not in body


def test_missing_bearer_token_returns_unauthorized(client):
    resp = client.get("/api/v1/users/1")
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == 401
    assert body["msg"] == Status.UNAUTHORIZED_ERROR.msg
    assert body["data"] is None
    assert body["request_id"] == resp.headers["X-Request-ID"]
    assert "missing" in body["error"]


def test_list_users_admin_returns_success_payload(client):
    svc = override_user_service(client, list_user={"items": [{"id": "1"}], "total": 1})
    override_current_user(client, role="admin")

    resp = client.get("/api/v1/users?page=1&size=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == Status.SUCCESS.code
    assert body["msg"] == Status.SUCCESS.msg
    assert body["data"] == {"items": [{"id": "1"}], "total": 1}
    assert body["request_id"] == resp.headers["X-Request-ID"]
    svc.list_user.assert_awaited_once()
    req_arg = svc.list_user.await_args.args[0]
    assert (req_arg.page, req_arg.size) == (1, 10)


def test_list_users_non_admin_returns_permission_error(client):
    svc = override_user_service(client, list_user={"items": [], "total": 0})
    override_current_user(client, role="user")

    resp = client.get("/api/v1/users")
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == Status.USER_PERMISSION_ERROR.code
    assert body["msg"] == Status.USER_PERMISSION_ERROR.msg
    assert body["data"] is None
    svc.list_user.assert_not_awaited()


def test_create_user_returns_created_id(client):
    svc = override_user_service(client, create_user={"id": "99"})
    payload = {"phone": "13800138000", "password": "abc12345"}

    resp = client.post("/api/v1/users", json=payload)
    assert resp.status_code == 200
    assert resp.json()["data"] == {"id": "99"}
    svc.create_user.assert_awaited_once()
    created = svc.create_user.await_args.args[0]
    assert created.phone == payload["phone"]
    assert created.password == payload["password"]


def test_create_user_invalid_phone_returns_validation_error(client):
    svc = override_user_service(client, create_user={"id": "99"})

    resp = client.post("/api/v1/users", json={"phone": "123", "password": "abc"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == Status.VALIDATION_ERROR.code
    assert "phone" in body["msg"]
    assert body["request_id"] == resp.headers["X-Request-ID"]
    svc.create_user.assert_not_awaited()


def test_get_update_delete_user_with_admin(client):
    svc = override_user_service(
        client,
        get_user={"id": "42", "nickname": "Tom"},
        update_user={"id": "42"},
        delete_user={"id": "42"},
    )
    override_current_user(client, role="admin")

    got = client.get("/api/v1/users/42")
    assert got.json()["data"] == {"id": "42", "nickname": "Tom"}
    svc.get_user.assert_awaited_once_with("42")

    updated = client.put("/api/v1/users/42", json={"nickname": "Jerry"})
    assert updated.json()["data"] == {"id": "42"}
    args, kwargs = svc.update_user.await_args
    assert kwargs == {"user_id": "42"}
    assert args[0].nickname == "Jerry"

    deleted = client.delete("/api/v1/users/42")
    assert deleted.json()["data"] == {"id": "42"}
    svc.delete_user.assert_awaited_once_with("42")


def test_delete_user_non_admin_returns_permission_error(client):
    svc = override_user_service(client, delete_user={"id": "42"})
    override_current_user(client, role="user")

    resp = client.delete("/api/v1/users/42")
    assert resp.status_code == 403
    assert resp.json()["code"] == Status.USER_PERMISSION_ERROR.code
    svc.delete_user.assert_not_awaited()


def test_login_sets_refresh_cookie_and_hides_refresh_fields(client):
    svc = override_user_service(
        client,
        auth_login={
            "access_token": "access-1",
            "token_type": "bearer",
            "expires_in": 7200,
            "user_info": {"id": "7", "role": "user"},
            "refresh_token": "refresh-1",
            "refresh_expires_in": 3600,
        },
    )

    resp = client.post(
        "/api/v1/users/auth/login",
        json={"phone": "13800138000", "password": "abc12345"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["data"]) == {"access_token", "token_type", "expires_in", "user_info"}
    cookie = resp.headers["set-cookie"]
    assert "x_refresh_token=refresh-1" in cookie
    assert "httponly" in cookie.lower()
    assert "path=/api" in cookie.lower()
    svc.auth_login.assert_awaited_once()


def test_logout_clears_refresh_cookie(client):
    svc = override_user_service(client, auth_logout={"id": "7"})
    override_current_user(client, user_id="7")

    resp = client.post("/api/v1/users/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["data"] == {"id": "7"}
    cookie = resp.headers["set-cookie"]
    assert "x_refresh_token=" in cookie
    assert "max-age=0" in cookie.lower()
    svc.auth_logout.assert_awaited_once_with("7")


def test_refresh_returns_new_token_and_cookie(client):
    svc = override_user_service(
        client,
        auth_refresh={
            "access_token": "access-2",
            "token_type": "bearer",
            "expires_in": 7200,
            "refresh_token": "refresh-2",
            "refresh_expires_in": 3600,
        },
    )
    override_refresh_user(client, user_id="7")

    resp = client.post("/api/v1/users/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"] == "access-2"
    assert "x_refresh_token=refresh-2" in resp.headers["set-cookie"]
    svc.auth_refresh.assert_awaited_once_with("7")


def test_custom_exception_returns_wrapped_failure(client):
    deps = importlib.import_module("app.api.deps")

    def deny():
        raise CustomException(status=Status.FORBIDDEN_ERROR, msg="custom deny")

    client.app.dependency_overrides[deps.get_current_user] = deny
    resp = client.get("/api/v1/users/1")
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == Status.FORBIDDEN_ERROR.code
    assert body["msg"] == "custom deny"
    assert body["request_id"] == resp.headers["X-Request-ID"]


def test_unhandled_exception_returns_wrapped_500(client, monkeypatch):
    deps = importlib.import_module("app.api.deps")
    middleware = importlib.import_module("app.core.middleware")
    monkeypatch.setattr(middleware, "_expose_error", lambda: False)

    def boom():
        raise RuntimeError("boom-in-test")

    client.app.dependency_overrides[deps.get_current_user] = boom
    resp = client.get("/api/v1/users/1")

    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == Status.INTERNAL_SERVER_ERROR.code
    assert body["msg"] == Status.INTERNAL_SERVER_ERROR.msg
    assert body["error"] is None
    assert body["request_id"] == resp.headers["X-Request-ID"]


def test_unhandled_exception_exposes_detail_in_debug(client, monkeypatch):
    deps = importlib.import_module("app.api.deps")
    middleware = importlib.import_module("app.core.middleware")
    monkeypatch.setattr(middleware, "_expose_error", lambda: True)

    def boom():
        raise RuntimeError("debug-detail")

    client.app.dependency_overrides[deps.get_current_user] = boom
    resp = client.get("/api/v1/users/1")

    assert resp.status_code == 500
    assert "debug-detail" in resp.json()["error"]


def test_cors_preflight_returns_allow_headers(client):
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://example.test",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Request-ID",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] in {"*", "http://example.test"}
    assert "GET" in resp.headers["access-control-allow-methods"]
    assert "x-request-id" in resp.headers["access-control-allow-headers"].lower()


def test_cors_warns_on_wildcard_with_credentials(client, monkeypatch):
    warnings = []
    monkeypatch.setattr(g.logger, "warning", lambda msg: warnings.append(msg))
    CorsMiddleware(app=client.app)

    assert any("allow_origins" in str(msg) for msg in warnings)
