"""SQLModel Item 模型"""

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, Relationship, SQLModel

from app.models.user import User


# ---------- 数据库表模型 ----------
class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: int | None = SQLField(default=None, primary_key=True)
    title: str = SQLField(max_length=100)
    description: str | None = SQLField(default=None)
    owner_id: int = SQLField(foreign_key="users.id")

    owner: User = Relationship(back_populates="items")


# ---------- 请求/响应 Schema ----------
class ItemCreate(BaseModel):
    """创建 Item"""

    title: str = Field(description="标题")
    description: str | None = Field(default=None, description="描述")


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
