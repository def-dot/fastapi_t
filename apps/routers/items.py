"""Item 路由 - 完整 CRUD，需要认证"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from apps.core.database import get_db
from apps.core.logging import get_logger
from apps.core.security import get_current_user
from apps.models.item import Item
from apps.models.user import User
from apps.schemas.schemas import (
    RESPONSE_401,
    RESPONSE_403,
    RESPONSE_404,
    ItemCreate,
    ItemOut,
    ItemUpdate,
    Page,
    ResponseBase,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/items", tags=["Item"], dependencies=[Depends(get_current_user)])


@router.post(
    "/",
    response_model=ResponseBase[ItemOut],
    status_code=status.HTTP_201_CREATED,
    responses={**RESPONSE_401},
)
async def create_item(
    item_in: ItemCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """创建 Item"""
    item = Item(**item_in.model_dump(), owner_id=current_user.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    logger.info("Item created: id=%d by user=%s", item.id, current_user.username)
    return ResponseBase(code=status.HTTP_201_CREATED, data=item)


@router.get("/", response_model=ResponseBase[Page[ItemOut]], responses={**RESPONSE_401})
async def list_items(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """获取 Item 列表（分页）"""
    total_result = await db.execute(select(func.count(Item.id)))
    total = total_result.scalar_one()
    result = await db.execute(select(Item).offset(skip).limit(limit))
    return ResponseBase(data=Page(items=result.scalars().all(), total=total))


@router.get("/me", response_model=ResponseBase[Page[ItemOut]], responses={**RESPONSE_401})
async def list_my_items(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的 Item 列表"""
    q = select(Item).where(Item.owner_id == current_user.id)
    total_result = await db.execute(select(func.count(Item.id)).where(Item.owner_id == current_user.id))
    total = total_result.scalar_one()
    result = await db.execute(q.offset(skip).limit(limit))
    return ResponseBase(data=Page(items=result.scalars().all(), total=total))


@router.get("/{item_id}", response_model=ResponseBase[ItemOut], responses={**RESPONSE_401, **RESPONSE_404})
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个 Item"""
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item 不存在")
    return ResponseBase(data=item)


@router.put(
    "/{item_id}",
    response_model=ResponseBase[ItemOut],
    responses={**RESPONSE_401, **RESPONSE_403, **RESPONSE_404},
)
async def update_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新 Item（仅所有者可操作）"""
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item 不存在")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此 Item")

    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    logger.info("Item updated: id=%d by user=%s", item.id, current_user.username)
    return ResponseBase(data=item)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**RESPONSE_401, **RESPONSE_403, **RESPONSE_404},
)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除 Item（仅所有者可操作）"""
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item 不存在")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此 Item")

    await db.delete(item)
    await db.commit()
    logger.info("Item deleted: id=%d by user=%s", item_id, current_user.username)
