from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError, InvalidSubjectError
from datetime import timedelta, datetime, timezone
from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlmodel import select
from app.models import User
from app.schemas import UserCreate
from app.database import get_session
from app.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Creates a JWT token
def create_access_token(*, subject: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": subject,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expires_delta
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Takes a JWT token and returns the user associated with it. Passed as a dependency in routes.
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           db: Annotated[AsyncSession, Depends(get_session)]) -> User:
    
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials",
                                          headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (InvalidTokenError, InvalidSubjectError, ValueError):
        raise credentials_exception

    user = await db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user


# Takes a username and password and stores it in db (with the password hashed)
async def signup(user: UserCreate, db: AsyncSession) -> User:
    new_user = User(email=user.email, password_hash="", username=user.username)
    new_user.set_password(user.password)

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Username or email already exists")

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    
    return new_user


# Takes login data according to the OAuth2PasswordRequestForm schema, then creates a JWT token if
# the credentials are correct and returns it.
async def login(data: OAuth2PasswordRequestForm, db: AsyncSession):
    statement = select(User).where(User.username == data.username)
    try:
        user = (await db.exec(statement)).one_or_none()

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if user is None or not user.check_password(data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")

    token = create_access_token(subject=str(user.id),
                                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {"access_token": token, "token_type": "bearer"}