from fastapi import FastAPI, status, HTTPException, Path
from dummy_data import applications
from schemas import ApplicationCreate, ApplicationRead
from datetime import datetime, UTC
from typing import Annotated

app = FastAPI()

@app.get("/applications", response_model=list[ApplicationRead])
async def get_applications() -> list[ApplicationRead]:
    return applications

@app.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_applications(application: ApplicationCreate) -> ApplicationRead:

    new_app = {
        "id": len(applications) + 1,
        "company": application.company,
        "role": application.role,
        "status": application.status,
        "job_url": application.job_url,
        "notes": application.notes,
        "applied_at": datetime.now(UTC) if application.status != "saved" else None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    applications.append(new_app)
    return new_app

@app.get("/applications/{id}", response_model=ApplicationRead)
async def get_application(id: Annotated[int, Path(ge=1)]) -> ApplicationRead:
    try:
        return applications[id - 1]
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)