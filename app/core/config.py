"""应用配置 - 使用 pydantic Settings 管理环境变量"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "FastAPI Demo"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://postgres:sj1107@localhost:5432/fastapi_demo"

    # JWT
    SECRET_KEY: str = "change-me-to-a-random-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gunicorn
    WORKERS: int = 4
    BIND: str = "0.0.0.0:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
