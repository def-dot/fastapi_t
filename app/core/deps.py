"""依赖注入 — 集中管理所有 FastAPI Depends 并声明 Annotated 类型别名"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

SessionDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
