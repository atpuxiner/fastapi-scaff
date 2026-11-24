from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
client_ip_var: ContextVar[str] = ContextVar("client_ip", default="-")
