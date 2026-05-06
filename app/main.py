"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import access_log_middleware
from app.routers import auth, items, users
from app.schemas.schemas import ResponseBase

logger = get_logger(__name__)

# ---------- lifespan：应用启动/关闭时执行 ----------
@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    setup_logging()
    try:
        import subprocess

        subprocess.check_call(["alembic", "upgrade", "head"])
        logger.info("%s started — DB migrated", settings.APP_NAME)
    except Exception:
        logger.critical("Failed to initialize database", exc_info=True)
        raise
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    description="FastAPI Demo — 用户认证与 CRUD 示例项目",
    swagger_ui_parameters={"persistAuthorization": True},
)

# ---------- 异常处理 ----------
register_exception_handlers(app)

# ---------- 中间件 ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(access_log_middleware)

# ---------- 注册路由 ----------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)


# ---------- 健康检查 ----------
@app.get("/health", tags=["系统"], response_model=ResponseBase[dict[str, Any]])
async def health_check() -> Any:
    return ResponseBase(data={"status": "ok"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
