"""数据库初始化脚本 — 创建初始数据"""

import asyncio

from sqlmodel import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.item import Item  # noqa: F401 — 触发 SQLAlchemy 关联解析
from app.models.user import User


async def create_initial_data() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.exec(select(User).where(User.username == "admin"))
        if not result.first():
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin"),
            )
            db.add(admin)
            await db.commit()
            print("Admin user created (username: admin, password: admin)")
        else:
            print("Admin user already exists, skipped")


if __name__ == "__main__":
    asyncio.run(create_initial_data())
