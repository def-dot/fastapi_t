"""测试配置 - 使用 SQLite 内存数据库"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.main import app
from app.models.item import Item  # noqa: F401
from app.models.user import User  # noqa: F401

# SQLite 内存数据库（异步）
TEST_DATABASE_URL = "sqlite+aiosqlite://"
test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as db:
        yield db


# 替换应用的数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """每个测试前建表，测试后清表"""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """异步 HTTP 测试客户端"""
    print(f"\nDEBUG: app.lifespan_context is {app.router.lifespan_context}")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient) -> str:
    """注册一个用户并返回 access_token"""
    await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "secret123",
        },
    )
    resp = await client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "secret123",
        },
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token: str) -> dict:
    """带 Bearer token 的请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_engine():
    """所有测试结束后，彻底关闭引擎连接池"""
    yield
    await test_engine.dispose()
