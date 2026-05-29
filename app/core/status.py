from enum import Enum


class Status(Enum):
    # =========== 基础状态 ===========
    SUCCESS = (0, "操作成功", 200)
    FAILURE = (1, "操作失败", 400)

    # =========== HTTP 标准错误 ===========
    PARAMS_ERROR = (400, "参数错误", 400)
    UNAUTHORIZED_ERROR = (401, "认证失败，请先登录", 401)
    FORBIDDEN_ERROR = (403, "权限不足，无法访问", 403)
    NOT_FOUND_ERROR = (404, "资源未找到", 404)
    VALIDATION_ERROR = (422, "数据校验失败", 422)
    INTERNAL_SERVER_ERROR = (500, "服务开小差了，请稍后再试", 500)

    # =========== 业务错误（10000 开始） ===========
    # 【通用业务】10xxx
    RECORD_NOT_EXIST_ERROR = (10000, "记录不存在", 404)
    RECORD_EXISTS_ERROR = (10001, "记录已存在", 400)
    # 【用户模块】101xx
    USER_OR_PASSWORD_ERROR = (10101, "用户名或密码错误", 400)
    USER_ABNORMAL_ERROR = (10102, "用户已被禁用或删除", 403)
    USER_PERMISSION_ERROR = (10103, "用户权限不足", 403)

    @property
    def code(self):
        return self.value[0]

    @property
    def msg(self):
        return self.value[1]

    @property
    def status_code(self):
        return self.value[2]

    @classmethod
    def from_status_code(cls, status_code: int) -> "Status":
        mapping = {
            400: cls.PARAMS_ERROR,
            401: cls.UNAUTHORIZED_ERROR,
            403: cls.FORBIDDEN_ERROR,
            404: cls.NOT_FOUND_ERROR,
            422: cls.VALIDATION_ERROR,
            500: cls.INTERNAL_SERVER_ERROR,
        }
        return mapping.get(status_code, cls.FAILURE)

    @classmethod
    def collect_status(cls):
        text = ""
        for s in cls:
            text += f"{s.code:<8} {s.status_code:<8} {s.msg}\n"
        return text


if __name__ == "__main__":
    print(Status.collect_status())
