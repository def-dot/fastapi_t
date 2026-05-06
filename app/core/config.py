"""应用配置 - 使用 pydantic Settings 管理环境变量"""

import os

from pydantic_settings import BaseSettings

APP_ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Demo"
    DB_DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 4

    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # JWT
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {"env_file": f".env.{APP_ENV}", "env_file_encoding": "utf-8"}


settings = Settings()
