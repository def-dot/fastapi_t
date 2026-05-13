"""
外部 API 路由示例 - 展示如何使用 Tenacity 进行重试
"""

from typing import Any, cast

import httpx
from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.schemas.schemas import RESPONSE_401, ResponseBase
from app.utils.retry import api_retry

logger = get_logger(__name__)
router = APIRouter(prefix="/external", tags=["外部API"], dependencies=[Depends(get_current_user)])


@api_retry
async def call_external_api(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    调用外部 API 的函数，带有自动重试
    使用 api_retry 装饰器，在连接失败或超时时自动重试
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com{endpoint}", params=params or {}, timeout=10.0)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


@router.get("/weather/{city}", response_model=ResponseBase[dict[str, Any]], responses={**RESPONSE_401})
async def get_weather(city: str) -> Any:
    """
    获取天气信息 - 展示 API 重试的使用
    在网络不稳定时，api_retry 装饰器会自动重试请求
    """
    weather_data = await call_external_api(f"/weather/{city}")
    return ResponseBase(data=weather_data)
