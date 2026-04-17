"""认证路由 - 注册 / 登录"""
import time
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.schemas import LoginRequest, RefreshTokenRequest, Token, UserCreate, UserOut

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["认证"])


def send_welcome_email(email: str, username: str):
    """后台任务：发送欢迎邮件"""
    # 实际项目中替换为真实邮件发送逻辑
    logger.info("Welcome email sent to %s for user %s", email, username)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """注册新用户"""
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="邮箱已注册")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(send_welcome_email, user.email, user.username)
    logger.info("User registered: %s", user.username)
    return user


@router.post("/login", response_model=Token)
async def login(user_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录获取 JWT Token - 支持用户名或邮箱登录"""
    result = await db.execute(
        select(User).where(
            (User.username == user_in.username)
            | (User.email == user_in.username)
        )
    )
    user = result.scalars().first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    logger.info("User logged in: %s", user.username)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh(body: RefreshTokenRequest):
    """用 refresh token 换取新的 access token 和 refresh token"""
    payload = decode_access_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 refresh token")

    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 refresh token")

    access_token = create_access_token(data={"sub": username})
    new_rt = create_refresh_token(data={"sub": username})
    return Token(access_token=access_token, refresh_token=new_rt)
