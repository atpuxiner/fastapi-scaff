from app.api.status import Status


class CustomException(Exception):

    def __init__(
            self,
            msg: str = None,
            code: int = None,
            error: str | Exception | None = None,
            data: dict | list | str | None = None,
            status: Status = Status.FAILURE,
    ):
        self.msg = msg or status.msg
        self.code = code or status.code
        self.error = error
        self.data = data
        self.status = status
        super().__init__(self.msg, self.code)

    def __str__(self) -> str:
        return f"{self.code} - {self.msg}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ({self.code!r}, {self.msg!r})>"
