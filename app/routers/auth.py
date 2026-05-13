"""认证路由 - 注册 / 登录"""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlmodel import select

from app.core.deps import OAuth2Form, SessionDep
from app.core.logging import get_logger
from app.core.security import (
    DUMMY_HASHED_PASSWORD,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_and_update_password,
)
from app.models.user import User, UserCreate, UserOut
from app.schemas.schemas import (
    RESPONSE_400,
    RESPONSE_401,
    RESPONSE_422,
    RefreshTokenRequest,
    ResponseBase,
    Token,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["认证"])


def send_welcome_email(email: str, username: str) -> None:
    """后台任务：发送欢迎邮件"""
    logger.info("Welcome email sent to %s for user %s", email, username)


@router.post(
    "/register",
    response_model=ResponseBase[UserOut],
    status_code=status.HTTP_201_CREATED,
    responses={**RESPONSE_400, **RESPONSE_422},
)
async def register(user_in: UserCreate, background_tasks: BackgroundTasks, db: SessionDep) -> Any:
    """注册新用户"""
    result = await db.exec(select(User).where(User.username == user_in.username))
    if result.first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    result = await db.exec(select(User).where(User.email == user_in.email))
    if result.first():
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
    return ResponseBase(code=status.HTTP_201_CREATED, data=user)


@router.post(
    "/login",
    response_model=ResponseBase[Token],
    responses={**RESPONSE_401},
)
async def login(form: OAuth2Form, db: SessionDep) -> Any:
    """登录获取 JWT Token - 支持用户名或邮箱登录（OAuth2 兼容）"""
    result = await db.exec(select(User).where((User.username == form.username) | (User.email == form.username)))
    user = result.first()

    # 无论用户是否存在都执行一次哈希验证，防止通过响应时间枚举用户名
    password_hash = user.hashed_password if user else DUMMY_HASHED_PASSWORD
    password_ok, updated_hash = verify_and_update_password(form.password, password_hash)
    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 哈希算法过旧时自动升级
    if updated_hash:
        user.hashed_password = updated_hash
        db.add(user)
        await db.commit()
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    logger.info("User logged in: %s", user.username)
    return ResponseBase(data=Token(access_token=access_token, refresh_token=refresh_token))


@router.post(
    "/refresh",
    response_model=ResponseBase[Token],
    responses={**RESPONSE_401},
)
async def refresh(body: RefreshTokenRequest) -> Any:
    """用 refresh token 换取新的 access token 和 refresh token"""
    payload = decode_access_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 refresh token")

    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 refresh token")

    access_token = create_access_token(data={"sub": username})
    new_rt = create_refresh_token(data={"sub": username})
    return ResponseBase(data=Token(access_token=access_token, refresh_token=new_rt))
