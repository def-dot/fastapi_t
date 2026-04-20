"""用户路由 - CRUD + 获取当前用户信息"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user, hash_password
from app.models.user import User, UserOut, UserUpdate
from app.schemas.schemas import (
    RESPONSE_401,
    RESPONSE_404,
    Page,
    ResponseBase,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/users", tags=["用户"], dependencies=[Depends(get_current_user)])


@router.get("/me", response_model=ResponseBase[UserOut], responses={**RESPONSE_401})
async def read_current_user(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return ResponseBase(data=current_user)


@router.get("/", response_model=ResponseBase[Page[UserOut]], responses={**RESPONSE_401})
async def list_users(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """获取用户列表（分页）"""
    total = (await db.exec(select(func.count(col(User.id))))).one()
    users = (await db.exec(select(User).offset(skip).limit(limit))).all()
    return ResponseBase(data=Page(items=users, total=total))


@router.get("/{user_id}", response_model=ResponseBase[UserOut], responses={**RESPONSE_401, **RESPONSE_404})
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个用户"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseBase(data=user)


@router.put("/me", response_model=ResponseBase[UserOut], responses={**RESPONSE_401})
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户信息"""
    if user_in.email is not None:
        current_user.email = user_in.email
    if user_in.password is not None:
        current_user.hashed_password = hash_password(user_in.password)
    await db.commit()
    await db.refresh(current_user)
    logger.info("User updated: %s", current_user.username)
    return ResponseBase(data=current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, responses={**RESPONSE_401})
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除当前用户"""
    await db.delete(current_user)
    await db.commit()
    logger.info("User deleted: %s", current_user.username)
