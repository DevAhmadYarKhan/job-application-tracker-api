from fastapi import APIRouter, Depends, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas import UserRead, UserCreate, UserLogin
from app.database import get_session
from app.services import auth as auth_service


router = APIRouter(tags=["authorization"])

@router.get("/me", response_model=UserRead)
async def me(request: Request, db: AsyncSession = Depends(get_session)) -> UserRead:
    return await auth_service.get_current_user(request=request, db=db)

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, request: Request, db: AsyncSession = Depends(get_session)) -> UserRead:
    return await auth_service.signup(user=user, request=request, db=db)

@router.post("/login", response_model=UserRead)
async def  login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_session)) -> UserRead:
    return await auth_service.login(data=data, request=request, db=db)

@router.get("/logout")
async def logout(request: Request):
    return await auth_service.logout(request)