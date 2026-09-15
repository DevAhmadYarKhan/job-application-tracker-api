from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from app.database import create_db
from app.routes import applications, auth

# Everything before yield runs at startup, everything after yield runs at shutdown. 
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key="SESSION_SECRET" # Insecure and will change this later
)

app.include_router(applications.router)
app.include_router(auth.router)