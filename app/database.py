from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config import DATABASE_URL


engine = create_async_engine(DATABASE_URL)

# Gives a session that allows for interacting with the database, we inject it into our routes
async def get_session():
    async with AsyncSession(engine) as session:
        yield session
