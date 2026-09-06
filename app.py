from fastapi import FastAPI, status, HTTPException, Path
from dummy_data import applications
from schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from datetime import datetime, UTC
from typing import Annotated

app = FastAPI()

@app.get("/applications", response_model=dict[int, ApplicationRead])
async def get_applications() -> dict[int, ApplicationRead]:
    return applications

@app.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_applications(application: ApplicationCreate) -> ApplicationRead:
    id= max(applications) + 1
    new_app = {
        "id": id,
        "company": application.company,
        "role": application.role,
        "status": application.status,
        "job_url": application.job_url,
        "notes": application.notes,
        "applied_at": datetime.now(UTC) if application.status != "saved" else None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }
    applications[id] = new_app
    return new_app

@app.get("/applications/{id}", response_model=ApplicationRead)
async def get_application(id: Annotated[int, Path(ge=1)]) -> ApplicationRead:
    try:
        return applications[id]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@app.delete("/applications/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(id: Annotated[int, Path(ge=1)]):
    try:
        applications.pop(id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@app.patch("/applications/{id}", response_model=ApplicationRead)
async def update_application(id: Annotated[int, Path(ge=1)], update: ApplicationUpdate) -> ApplicationRead:
    update_data = update.model_dump(exclude_unset=True)
    try:
        temp = applications[id].copy()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    temp.update(update_data)
    if temp["status"] == "saved" and temp["applied_at"] is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    applications[id] = temp
    return applications[id]