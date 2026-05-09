"""
外部 API 路由示例 - 展示如何使用 Tenacity 进行重试
"""

from typing import Any, cast

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import CurrentUser
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.schemas.schemas import RESPONSE_401, ResponseBase
from app.utils.retry import api_retry, api_retry_with_http_errors, db_retry

logger = get_logger(__name__)
router = APIRouter(prefix="/api/external", tags=["外部API"], dependencies=[Depends(get_current_user)])


@api_retry
async def call_external_api(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    """
    调用外部 API 的函数，带有自动重试
    使用 api_retry 装饰器，在连接失败或超时时自动重试
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com{endpoint}", params=params or {}, timeout=10.0)
        response.raise_for_status()
        return response.json()


@db_retry
async def get_user_with_retry(user_id: int, db: AsyncSession) -> dict[str, Any]:
    """
    从数据库获取用户，带有连接重试
    使用 db_retry 装饰器，在数据库连接问题时自动重试
    """
    # 这里应该是实际的数据库查询
    # 示例中我们模拟一个可能失败的操作

    from app.models.user import User

    user = await db.get(User, user_id)
    if not user:
        raise ValueError(f"用户 {user_id} 不存在")
    return {"user_id": user.id, "username": user.username, "email": user.email}


@router.get("/weather/{city}", response_model=ResponseBase[dict[str, Any]], responses={**RESPONSE_401})
async def get_weather(city: str, current_user: CurrentUser) -> Any:
    """
    获取天气信息 - 展示 API 重试的使用
    在网络不稳定时，api_retry 装饰器会自动重试请求
    """
    try:
        weather_data = await call_external_api(f"/weather/{city}")
        return ResponseBase(data=weather_data)
    except Exception as e:
        logger.error(f"获取天气信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"无法获取天气信息: {str(e)}"
        ) from e


@router.get("/user-profile/{user_id}", response_model=ResponseBase[dict[str, Any]], responses={**RESPONSE_401})
async def get_external_user_profile(user_id: int, current_user: CurrentUser) -> Any:
    """
    获取外部用户资料 - 展示带参数的 API 重试
    """
    try:
        profile = await call_external_api(f"/users/{user_id}", params={"include_details": "true"})
        return ResponseBase(data=profile)
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"外部服务不可用: {str(e)}") from e


@api_retry_with_http_errors
async def call_external_api_with_http_retry(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    调用外部 API 的函数，带有 HTTP 错误重试
    使用 api_retry_with_http_errors 装饰器，在连接失败、超时或 HTTP 错误时自动重试
    注意：这会重试所有 HTTP 错误，包括 4xx 和 5xx
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com{endpoint}", params=params or {}, timeout=10.0)
        response.raise_for_status()  # HTTP 错误也会触发重试
        return cast(dict[str, Any], response.json())


@router.post("/sync-data", response_model=ResponseBase[dict[str, Any]], responses={**RESPONSE_401})
async def sync_external_data(current_user: CurrentUser) -> Any:
    """
    同步外部数据 - 展示多个重试操作的组合使用
    """
    try:
        # 调用多个外部 API，每个都有独立的重试机制
        users_data = await call_external_api("/users")
        posts_data = await call_external_api("/posts")
        comments_data = await call_external_api("/comments")

        synced_data = {
            "users": len(users_data.get("data", [])),
            "posts": len(posts_data.get("data", [])),
            "comments": len(comments_data.get("data", [])),
            "synced_at": "2024-01-01T00:00:00Z",
        }

        logger.info(f"数据同步完成: {synced_data}")
        return ResponseBase(data=synced_data, msg="数据同步成功")

    except Exception as e:
        logger.error(f"数据同步失败: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"数据同步失败: {str(e)}") from e


@router.get("/data-with-retry/{endpoint}", response_model=ResponseBase[dict[str, Any]], responses={**RESPONSE_401})
async def get_data_with_http_retry(endpoint: str, current_user: CurrentUser) -> Any:
    """
    获取数据并重试 HTTP 错误 - 展示 api_retry_with_http_errors 的使用
    当外部 API 返回 5xx 错误时，会自动重试
    """
    try:
        data = await call_external_api_with_http_retry(f"/{endpoint}")
        return ResponseBase(data=data)
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"外部服务不可用: {str(e)}") from e
