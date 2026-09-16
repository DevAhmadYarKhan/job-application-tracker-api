from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from config import DATABASE_URL


engine = create_async_engine(DATABASE_URL)

# This function creates a database with all the tables defined according to SQLModel models
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Gives a session that allows for interacting with the database, we inject it into our routes
async def get_session():
    async with AsyncSession(engine) as session:
        yield session