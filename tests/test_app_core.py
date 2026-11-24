"""核心工具函数测试：状态码、统一响应、JWT/密码与 API Key。"""

import json

from app.core.context import request_id_var
from app.core.responses import Responses
from app.core.status import Status
from app.utils.api_key_util import gen_api_key
from app.utils.jwt_util import gen_jwt, gen_jwt_key, hash_password, verify_jwt, verify_password


def test_status_values_and_mapping():
    assert Status.SUCCESS.code == 0
    assert Status.SUCCESS.status_code == 200
    assert Status.USER_PERMISSION_ERROR.code == 10103
    assert Status.USER_PERMISSION_ERROR.status_code == 403
    assert Status.from_status_code(404) is Status.NOT_FOUND_ERROR
    assert Status.from_status_code(418) is Status.FAILURE


def test_responses_success_and_failure_share_request_id():
    token = request_id_var.set("unit-request-id")
    try:
        success = Responses.success(data={"ok": True}, status_code=201)
        failure = Responses.failure(status=Status.PARAMS_ERROR, error="bad input")
    finally:
        request_id_var.reset(token)

    success_payload = json.loads(success.body)
    failure_payload = json.loads(failure.body)
    assert success.status_code == 201
    assert success_payload == {
        "msg": Status.SUCCESS.msg,
        "code": Status.SUCCESS.code,
        "data": {"ok": True},
        "request_id": "unit-request-id",
    }
    assert failure.status_code == 400
    assert failure_payload["code"] == Status.PARAMS_ERROR.code
    assert failure_payload["error"] == "bad input"
    assert failure_payload["request_id"] == "unit-request-id"


def test_jwt_generation_and_verification():
    key = gen_jwt_key()
    token = gen_jwt({"id": "1", "role": "admin"}, key, typ="refresh", exp_seconds=60)
    payload = verify_jwt(token, key=key, typ="refresh")
    assert payload["id"] == "1"
    assert payload["typ"] == "refresh"

    try:
        verify_jwt(token, key=key, typ="access")
    except ValueError as exc:
        assert "Invalid token type" in str(exc)
    else:
        raise AssertionError("access token verification should reject a refresh token")


def test_password_hashing_and_api_key():
    hashed = hash_password("abc12345")
    assert hashed != "abc12345"
    assert verify_password("abc12345", hashed)
    assert not verify_password("wrong-password", hashed)

    key = gen_api_key(prefix="sk-", length=20)
    assert key.startswith("sk-")
    assert len(key) == 23
