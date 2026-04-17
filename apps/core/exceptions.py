"""统一错误处理"""

import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.schemas.schemas import ResponseBase


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request.state.error_msg = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseBase(code=exc.status_code, msg=str(exc.detail)).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        detail = "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in errors)
        request.state.error_msg = f"参数校验失败: {detail}"
        return JSONResponse(
            status_code=422,
            content=ResponseBase(code=422, msg="参数校验失败", data={"detail": detail}).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request.state.error_msg = f"{exc}\n{traceback.format_exc()}"
        return JSONResponse(
            status_code=500,
            content=ResponseBase(code=500, msg="服务器内部错误").model_dump(),
        )
