"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.core.config import settings
from apps.core.database import Base, engine
from apps.core.exceptions import register_exception_handlers
from apps.core.logging import get_logger, setup_logging
from apps.core.middleware import access_log_middleware
from apps.routers import auth, items, users
from apps.schemas.schemas import ResponseBase

logger = get_logger(__name__)

# ---------- lifespan：应用启动/关闭时执行 ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("%s started — DB tables created", settings.APP_NAME)
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
    allow_origins=["*"],        # 生产环境请限制具体域名
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
@app.get("/health", tags=["系统"], response_model=ResponseBase[dict])
async def health_check():
    return ResponseBase(data={"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# 生产环境启动方式：
#   gunicorn -c gunicorn.conf.py main:app
