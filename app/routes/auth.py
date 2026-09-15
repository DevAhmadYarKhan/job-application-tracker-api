from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
from app.schemas import UserRead, UserCreate, UserLogin
from app.database import get_session
from app.services import auth as auth_service


router = APIRouter(tags=["authorization"])

@router.get("/me", response_model=UserRead)
async def me(user: Annotated[User, Depends(auth_service.get_current_user)]) -> UserRead:
    return user

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_session)) -> UserRead:
    return await auth_service.signup(user=user, db=db)

@router.post("/token")
async def  login(data: Annotated[OAuth2PasswordRequestForm, Depends()],
                 db: AsyncSession = Depends(get_session)):
    return await auth_service.login(data=data, db=db)