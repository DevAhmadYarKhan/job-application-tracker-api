from fastapi import FastAPI, status, HTTPException, Path, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError 
from database import create_db, get_session
from models import Job
from dummy_data import applications
from schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from datetime import datetime, UTC
from typing import Annotated

app = FastAPI()
create_db()

# Return all applications. We could use list[Job] itself as the response_model, but I am not sure about it yet
@app.get("/applications", response_model=list[ApplicationRead])
async def get_applications(session: Session = Depends(get_session)) -> list[ApplicationRead]:
    statement = select(Job)
    results = session.exec(statement)
    return results.all()

# Create an application. applied_at and updated_at is set to current time unless status is saved, can edit later
# using patch endpoint, but we could also allow setting them in this post endpoint. Not sure yet if I should
# change the implementation to do that yet.
@app.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_applications(application: ApplicationCreate,
                              session: Session = Depends(get_session)) -> ApplicationRead:
    app = Job(company=application.company, role=application.role, status=application.status,
                      job_url=application.job_url, notes=application.notes,
                      applied_at=datetime.now(UTC) if application.status != "saved" else None)
    try:
        session.add(app)
        session.commit()
        session.refresh(app)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return app

# Get a specific application by id
@app.get("/applications/{id}", response_model=ApplicationRead)
async def get_application(id: Annotated[int, Path(ge=1)],
                          session: Session = Depends(get_session)) -> ApplicationRead:
    try:
        application = session.get(Job, id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return application


# Delete a specific application by id
@app.delete("/applications/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(id: Annotated[int, Path(ge=1)]):
    try:
        applications.pop(id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

# Update a specific application's details (i.e. a patch) by id
@app.patch("/applications/{id}", response_model=ApplicationRead)
async def update_application(id: Annotated[int, Path(ge=1)], update: ApplicationUpdate) -> ApplicationRead:
    update_data = update.model_dump(exclude_unset=True) # Create dictionary with only fields that were provided
    try:
        temp = applications[id].copy()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    temp.update(update_data)
    if temp["status"] == "saved" and temp["applied_at"] is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    applications[id] = temp
    return applications[id]