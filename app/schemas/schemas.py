"""Pydantic 请求/响应 Schema"""

from pydantic import BaseModel, Field


class ResponseBase[T](BaseModel):
    """统一响应格式"""

    code: int = Field(default=200, description="业务状态码")
    msg: str = Field(default="ok", description="提示信息")
    data: T | None = Field(default=None, description="响应数据")


# 常见错误 responses 字典，路由可按需引用
RESPONSE_400 = {
    400: {
        "model": ResponseBase[None],
        "description": "请求错误",
        "content": {"application/json": {"example": {"code": 400, "msg": "请求错误", "data": None}}},
    }
}
RESPONSE_401 = {
    401: {
        "model": ResponseBase[None],
        "description": "未认证",
        "content": {"application/json": {"example": {"code": 401, "msg": "未认证", "data": None}}},
    }
}
RESPONSE_403 = {
    403: {
        "model": ResponseBase[None],
        "description": "无权限",
        "content": {"application/json": {"example": {"code": 403, "msg": "无权限", "data": None}}},
    }
}
RESPONSE_404 = {
    404: {
        "model": ResponseBase[None],
        "description": "资源不存在",
        "content": {"application/json": {"example": {"code": 404, "msg": "资源不存在", "data": None}}},
    }
}
RESPONSE_422 = {
    422: {
        "model": ResponseBase[None],
        "description": "参数校验失败",
        "content": {"application/json": {"example": {"code": 422, "msg": "参数校验失败", "data": None}}},
    }
}


class Page[T](BaseModel):
    """分页数据"""

    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总数量")


# ---------- Auth ----------
class Token(BaseModel):
    """JWT Token"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenData(BaseModel):
    username: str | None = None


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(description="刷新令牌")
