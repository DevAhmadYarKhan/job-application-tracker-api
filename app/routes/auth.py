from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas import UserRead
from app.database import get_session
from app.services import auth as auth_service


router = APIRouter(tags=["authorization"])

@router.get("/me", response_model=UserRead)
async def me(request: Request, db: AsyncSession = Depends(get_session)) -> UserRead:
    return await auth_service.get_current_user(request=request, db=db)