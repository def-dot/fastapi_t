"""应用配置 - 使用 pydantic Settings 管理环境变量"""

import os

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

APP_ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Demo"
    DB_DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 4

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "fastpi_demo"

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # JWT
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {"env_file": f".env.{APP_ENV}", "env_file_encoding": "utf-8"}


settings = Settings()
