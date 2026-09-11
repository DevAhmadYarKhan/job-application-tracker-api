from fastapi import FastAPI
from app.database import create_db
from app.routes import applications

create_db()
app = FastAPI()

app.include_router(applications.router)