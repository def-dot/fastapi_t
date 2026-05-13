"""健康检查路由"""

from typing import Any

from fastapi import APIRouter

from app.schemas.schemas import ResponseBase

router = APIRouter(tags=["系统"])


@router.get("/health", response_model=ResponseBase[dict[str, Any]])
async def health_check() -> Any:
    return ResponseBase(data={"status": "ok"})
