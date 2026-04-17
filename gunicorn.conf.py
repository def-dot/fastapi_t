"""Gunicorn 配置 - 多进程管理 Uvicorn worker"""

from apps.core.config import settings

# 监听地址
bind = settings.BIND

# Worker 数量
workers = settings.WORKERS

# 使用 uvicorn worker
worker_class = "uvicorn.workers.UvicornWorker"

# 每个 worker 的线程数（uvicorn 是异步的，无需多线程）
threads = 1

# Worker 超时（秒）
timeout = 120

# 优雅重启超时
graceful_timeout = 30

# 最大并发请求数（0 = 无限制）
worker_connections = 1000

# 守护进程
daemon = False

# PID 文件
pidfile = "logs/gunicorn.pid"

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = settings.LOG_LEVEL.lower()

# 启动前预热
preload_app = True

# Worker 最大请求数后重启（防止内存泄漏）
max_requests = 5000
max_requests_jitter = 500
