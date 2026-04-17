"""Pydantic 请求/响应 Schema"""

from pydantic import BaseModel, EmailStr, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """分页响应"""
    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总数量")


# ---------- Auth ----------
class Token(BaseModel):
    """JWT Token 响应"""
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


class LoginRequest(BaseModel):
    """登录请求 - 支持用户名或邮箱"""
    username: str = Field(description="用户名或邮箱", examples=["alice"])
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
    """用户信息响应"""
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
    """Item 响应"""
    id: int = Field(description="Item ID")
    title: str = Field(description="标题")
    description: str | None = Field(description="描述")
    owner_id: int = Field(description="所有者 ID")

    model_config = {"from_attributes": True}
