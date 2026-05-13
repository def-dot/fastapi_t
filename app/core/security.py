"""JWT 认证工具"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Argon2 优先用于新哈希，同时兼容验证旧 bcrypt 哈希
pwd_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hash.verify(plain, hashed)


def verify_and_update_password(plain: str, hashed: str) -> tuple[bool, str | None]:
    return pwd_hash.verify_and_update(plain, hashed)


DUMMY_HASHED_PASSWORD = hash_password("dummy-password-for-timing-attack-prevention")


# ---------- JWT ----------
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """生成 refresh token（无状态 JWT）"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """生成密码重置 token（1 小时有效）"""
    return jwt.encode(
        {"sub": email, "exp": datetime.now(UTC) + timedelta(hours=1), "type": "reset"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_password_reset_token(token: str) -> str:
    """验证密码重置 token，返回邮箱"""
    payload = decode_access_token(token)
    if payload.get("type") != "reset":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的重置令牌")
    email: str | None = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的重置令牌")
    return email


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


# ---------- 依赖注入：获取当前用户 ----------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据")

    result = await db.exec(select(User).where(User.username == username))
    user = result.first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user
