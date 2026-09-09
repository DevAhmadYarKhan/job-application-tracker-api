from fastapi import FastAPI, status, HTTPException, Path, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database import create_db, get_session
from models import Application
from dummy_data import applications
from schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from datetime import datetime, UTC
from typing import Annotated, Literal

app = FastAPI()
create_db()

# Return all applications. We could use list[Application] itself as the response_model, but I am not sure about it yet
@app.get("/applications", response_model=list[ApplicationRead])
async def get_applications(status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None,
                           sort_by: Literal["applied_at", "created_at", "updated_at"] | None = None,
                           order: Literal["asc", "desc"] = "asc",
                           session: Session = Depends(get_session)) -> list[ApplicationRead]:
    statement = select(Application)
    if status:
        statement = statement.where(Application.status == status)
    if sort_by:
        column = getattr(Application, sort_by)
        statement = statement.order_by(column.desc() if order == "desc" else column.asc())
    results = session.exec(statement)
    return results.all()

# Create an application. applied_at and updated_at is set to current time unless status is saved, can edit later
# using patch endpoint, but we could also allow setting them in this post endpoint. Not sure yet if I should
# change the implementation to do that yet.
@app.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_applications(application: ApplicationCreate,
                              session: Session = Depends(get_session)) -> ApplicationRead:
    new_application = Application(company=application.company, role=application.role, status=application.status,
                      job_url=application.job_url, notes=application.notes,
                      applied_at=datetime.now(UTC) if application.status != "saved" else None)
    try:
        session.add(new_application)
        session.commit()
        session.refresh(new_application)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return new_application

# Get a specific application by id
@app.get("/applications/{id}", response_model=ApplicationRead)
async def get_application(id: Annotated[int, Path(ge=1)],
                          session: Session = Depends(get_session)) -> ApplicationRead:
    try:
        application = session.get(Application, id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return application


# Delete a specific application by id
@app.delete("/applications/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(id: Annotated[int, Path(ge=1)], session: Session = Depends(get_session)):
    try:
        application = session.get(Application, id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        session.delete(application)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

# Update a specific application's details (i.e. a patch) by id
@app.patch("/applications/{id}", response_model=ApplicationRead)
async def update_application(id: Annotated[int, Path(ge=1)], update: ApplicationUpdate,
                             session: Session = Depends(get_session)) -> ApplicationRead:
    application = session.get(Application, id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    update_data = update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(UTC)
    application.sqlmodel_update(update_data)
    try:
        session.add(application)
        session.commit()
        session.refresh(application)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return application
