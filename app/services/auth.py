from fastapi import HTTPException, status, Request
from sqlmodel import select
from app.models import User
from app.schemas import UserCreate, UserLogin
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


# Should ideally make this a dependency in other routes to reduce code
async def get_current_user(request: Request, db: AsyncSession) -> User:
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = await db.get(User, user_id)

    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    return user


async def signup(user: UserCreate, request: Request, db: AsyncSession) -> User:
    new_user = User(email=user.email, password_hash="", name=user.name)
    new_user.set_password(user.password)

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    request.session.clear()
    request.session["user_id"] = new_user.id
    return new_user


async def login(data: UserLogin, request: Request, db: AsyncSession) -> User:
    statement = select(User).where(User.email == data.email)

    try:
        user = (await db.exec(statement)).one_or_none()

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if user is None or not user.check_password(data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password")

    request.session.clear()
    request.session["user_id"] = user.id
    return user


async def logout(request: Request):
    request.session.clear()
    return {
        "message": "Logged out"
    }