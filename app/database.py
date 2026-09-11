from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

database_url = "sqlite+aiosqlite:///database.db"

engine = create_async_engine(database_url)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Gives a session that allows for interacting with the database, we inject it into our routes
async def get_session():
    async with AsyncSession(engine) as session:
        yield session