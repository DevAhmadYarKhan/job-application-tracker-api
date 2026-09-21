from fastapi import FastAPI
from app.routes import applications, auth

app = FastAPI()


app.include_router(applications.router)
app.include_router(auth.router)