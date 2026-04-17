"""日志配置"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from apps.core.config import settings


def setup_logging() -> None:
    """初始化应用日志 - 同时输出到控制台和轮转文件"""
    log_level = settings.LOG_LEVEL.upper()
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 确保日志目录存在
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        ),
    ]

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
    )

    # 关闭 uvicorn 自带 access log（已由中间件记录）
    logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL + 1)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """获取命名 logger"""
    return logging.getLogger(name)
