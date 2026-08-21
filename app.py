from fastapi import FastAPI
from dummy_data import applications
from schemas import ApplicationCreate, ApplicationRead
from datetime import datetime, UTC

app = FastAPI()

@app.get("/applications", response_model=list[ApplicationRead])
async def get_applications() -> list[ApplicationRead]:
    return applications

@app.post("/applications")
async def create_applications(application: ApplicationCreate):

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