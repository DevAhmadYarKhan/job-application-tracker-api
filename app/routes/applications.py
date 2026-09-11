from fastapi import status, HTTPException, Path, Depends, Query, APIRouter
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from datetime import datetime, UTC
from typing import Annotated, Literal
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database import get_session
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"],)

# Return all applications. We could use list[Application] itself as the response_model, but I am not sure about it yet
@router.get("/", response_model=list[ApplicationRead])
async def get_applications(status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None,
                           sort_by: Literal["applied_at", "created_at", "updated_at"] | None = None,
                           order: Literal["asc", "desc"] = "asc",
                           page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                           session: AsyncSession = Depends(get_session)) -> list[ApplicationRead]:
    statement = select(Application)
    if status:
        statement = statement.where(Application.status == status)
    if sort_by:
        column = getattr(Application, sort_by)
        statement = statement.order_by(column.desc() if order == "desc" else column.asc())
    statement = statement.offset((page - 1) * page_size).limit(page_size)
    results = await session.exec(statement)
    return results.all()

# Create an application. applied_at and updated_at is set to current time unless status is saved, can edit later
# using patch endpoint, but we could also allow setting them in this post endpoint. Not sure yet if I should
# change the implementation to do that yet.
@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_applications(application: ApplicationCreate,
                              session: AsyncSession = Depends(get_session)) -> ApplicationRead:
    new_application = Application(company=application.company, role=application.role, status=application.status,
                      job_url=application.job_url, notes=application.notes,
                      applied_at=datetime.now(UTC) if application.status != "saved" else None)
    try:
        session.add(new_application)
        await session.commit()
        await session.refresh(new_application)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return new_application

# Get statistics about the total number of applications and number of applications with each status type.
# Inefficient due to multiple queries, more efficient way to do it that I will defer for now because
# of SQLModel giving unexpected behaviour
@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    statement = select(func.count()).select_from(Application)
    try:
        total = await session.exec(statement).one()
        saved = await session.exec(statement.where(Application.status == "saved")).one()
        applied = await session.exec(statement.where(Application.status == "applied")).one()
        interview = await session.exec(statement.where(Application.status == "interview")).one()
        offer = await session.exec(statement.where(Application.status == "offer")).one()
        rejected = await session.exec(statement.where(Application.status == "rejected")).one()
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    stats = {
        "total": total,
        "saved": saved,
        "applied": applied,
        "interview": interview,
        "offer": offer,
        "rejected": rejected
    }
    return stats

# Get a specific application by id
@router.get("/{id}", response_model=ApplicationRead)
async def get_application(id: Annotated[int, Path(ge=1)],
                          session: AsyncSession = Depends(get_session)) -> ApplicationRead:
    try:
        application = await session.get(Application, id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return application


# Delete a specific application by id
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(id: Annotated[int, Path(ge=1)], session: AsyncSession = Depends(get_session)):
    try:
        application = await session.get(Application, id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await session.delete(application)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

# Update a specific application's details (i.e. a patch) by id
@router.patch("/{id}", response_model=ApplicationRead)
async def update_application(id: Annotated[int, Path(ge=1)], update: ApplicationUpdate,
                             session: AsyncSession = Depends(get_session)) -> ApplicationRead:
    application = await session.get(Application, id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    update_data = update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(UTC)
    application.sqlmodel_update(update_data)
    try:
        session.add(application)
        await session.commit()
        await session.refresh(application)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return application
