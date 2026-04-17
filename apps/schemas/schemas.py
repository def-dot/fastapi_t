"""Pydantic 请求/响应 Schema"""

from pydantic import BaseModel, EmailStr, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(default=200, description="业务状态码")
    msg: str = Field(default="ok", description="提示信息")
    data: T | None = Field(default=None, description="响应数据")


# 常见错误 responses 字典，路由可按需引用
RESPONSE_400 = {400: {"model": ResponseBase[None], "description": "请求错误", "content": {"application/json": {"example": {"code": 400, "msg": "请求错误", "data": None}}}}}
RESPONSE_401 = {401: {"model": ResponseBase[None], "description": "未认证", "content": {"application/json": {"example": {"code": 401, "msg": "未认证", "data": None}}}}}
RESPONSE_403 = {403: {"model": ResponseBase[None], "description": "无权限", "content": {"application/json": {"example": {"code": 403, "msg": "无权限", "data": None}}}}}
RESPONSE_404 = {404: {"model": ResponseBase[None], "description": "资源不存在", "content": {"application/json": {"example": {"code": 404, "msg": "资源不存在", "data": None}}}}}
RESPONSE_422 = {422: {"model": ResponseBase[None], "description": "参数校验失败", "content": {"application/json": {"example": {"code": 422, "msg": "参数校验失败", "data": None}}}}}

class Page(BaseModel, Generic[T]):
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


class UserCreate(BaseModel):
    """注册请求"""
    username: str = Field(description="用户名", examples=["alice"])
    email: EmailStr = Field(description="邮箱", examples=["alice@example.com"])
    password: str = Field(description="密码", examples=["secret123"])


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(description="刷新令牌")


# ---------- User ----------
class UserUpdate(BaseModel):
    """更新用户信息"""
    email: EmailStr | None = Field(default=None, description="新邮箱")
    password: str | None = Field(default=None, description="新密码")


class UserOut(BaseModel):
    """用户信息"""
    id: int = Field(description="用户 ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    is_active: bool = Field(description="是否激活")

    model_config = {"from_attributes": True}


# ---------- Item ----------
class ItemCreate(BaseModel):
    """创建 Item"""
    title: str = Field(description="标题", examples=["My Item"])
    description: str | None = Field(default=None, description="描述", examples=["Some details"])


class ItemUpdate(BaseModel):
    """更新 Item"""
    title: str | None = Field(default=None, description="标题")
    description: str | None = Field(default=None, description="描述")


class ItemOut(BaseModel):
    """Item 信息"""
    id: int = Field(description="Item ID")
    title: str = Field(description="标题")
    description: str | None = Field(description="描述")
    owner_id: int = Field(description="所有者 ID")

    model_config = {"from_attributes": True}
