import multiprocessing
import os

# ========================
# 基础绑定
# ========================
bind = "0.0.0.0:8000"  # 监听地址；若用 Unix Socket：bind = "unix:/tmp/gunicorn.sock"

# ========================
# Worker 配置（核心）
# ========================
# 推荐公式：I/O 密集型应用（如 FastAPI）→ 2 * CPU + 1
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))  # async worker 软限制

# ========================
# 超时与生命周期
# ========================
timeout = 60  # 请求处理超时（秒），超过则 kill worker
keepalive = 5  # Keep-Alive 超时（秒）
graceful_timeout = 30  # SIGTERM 后等待时间（秒）
max_requests = 1000  # 每个 worker 处理 N 个请求后重启（防内存泄漏）
max_requests_jitter = 50  # 随机抖动（0~50），避免所有 worker 同时重启

# ========================
# 日志配置（容器友好：输出到 stdout/stderr）
# ========================
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"  # 访问日志 → stdout
errorlog = "-"  # 错误日志 → stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(T)s %(D)s'

# ========================
# 性能与安全
# ========================
preload_app = True  # 预加载应用，减少内存占用（fork 前加载）
forwarded_allow_ips = os.getenv(
    "FORWARDED_ALLOW_IPS",
    "*"
)
secure_scheme_headers = {"X-Forwarded-Proto": "https"}  # 识别 HTTPS

# ========================
# 进程与资源
# ========================
proc_name = "fastapi-app"  # ps/top 中显示的进程名
# pidfile = "/var/run/fastapi.pid"  # 容器中通常不需要，可注释
user = None  # 容器中通常以非 root 启动，由 Dockerfile 控制
group = None
tmp_upload_dir = None

# ========================
# 安全加固（可选但推荐）
# ========================
# limit_request_line = 4096         # 最大请求行长度（防 DoS）
# limit_request_fields = 100        # 最大 header 字段数
# limit_request_field_size = 8190   # 单个 header 最大大小
