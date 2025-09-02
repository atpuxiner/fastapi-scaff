from enum import Enum


class Status(Enum):
    SUCCESS = (0, '操作成功')
    FAILURE = (1, '操作失败')

    PARAMS_ERROR = (400, '参数错误')
    UNAUTHORIZED_ERROR = (401, '认证失败')
    # 建议：业务模块错误码从10000开始
    RECORD_NOT_EXIST_ERROR = (10000, '记录不存在')
    RECORD_EXISTS_ERROR = (10001, '记录已存在')
    USER_OR_PASSWORD_ERROR = (10002, '用户名或密码错误')

    @property
    def code(self):
        return self.value[0]

    @property
    def msg(self):
        return self.value[1]

    @classmethod
    def collect_status(cls):
        text = ""
        for s in cls:
            text += f"{s.code} {s.msg}\n"
        return text
