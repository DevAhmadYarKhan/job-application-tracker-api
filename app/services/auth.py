from fastapi import HTTPException, status, Request
from app.models import User
from sqlmodel.ext.asyncio.session import AsyncSession


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