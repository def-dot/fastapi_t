"""SQLModel 用户模型"""

from typing import TYPE_CHECKING

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item


# ---------- 数据库表模型 ----------
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=120, unique=True, index=True)
    hashed_password: str = Field(max_length=128)
    is_active: bool = Field(default=True)

    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# ---------- 请求/响应 Schema ----------
class UserCreate(SQLModel):
    """注册请求"""

    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    password: str = Field(description="密码")
    confirm_password: str = Field(description="确认密码")

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("密码和确认密码不一致")
        return self


class UserUpdate(SQLModel):
    """更新用户信息"""

    email: str | None = Field(default=None, description="新邮箱")
    password: str | None = Field(default=None, description="新密码")


class UserOut(SQLModel):
    """用户信息"""

    id: int = Field(description="用户 ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    is_active: bool = Field(description="是否激活")

    model_config = {"from_attributes": True}
