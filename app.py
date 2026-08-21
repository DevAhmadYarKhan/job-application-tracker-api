from fastapi import FastAPI
from dummy_data import applications

app = FastAPI()

@app.get("/applications")
async def get_applications():
    return applications