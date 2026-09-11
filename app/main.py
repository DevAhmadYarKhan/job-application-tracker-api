from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import create_db
from app.routes import applications

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(applications.router)