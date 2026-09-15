from fastapi import status, HTTPException, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
from datetime import datetime, UTC
from typing import Literal
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models import Application, User
from app.schemas import ApplicationCreate, ApplicationUpdate

# Returns all applications in Application table in db
async def get_applications(user: User,
                           db: AsyncSession,
                           app_status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None,
                           sort_by: Literal["applied_at", "created_at", "updated_at"] | None = None,
                           order: Literal["asc", "desc"] = "asc",
                           page: int = 1, page_size: int = 20) -> list[Application]:
    user_id = user.id

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not logged in")

    statement = select(Application).where(Application.user_id == user_id)
    if app_status:
        statement = statement.where(Application.status == app_status)

    if sort_by:
        column = getattr(Application, sort_by)
        statement = statement.order_by(column.desc() if order == "desc" else column.asc())

    statement = statement.offset((page - 1) * page_size).limit(page_size)
    results = await db.exec(statement)

    return results.all()

# Create an Application and adds it to Application table in db
async def create_application(user: User,
                             application: ApplicationCreate,
                             session: AsyncSession) -> Application:
    new_application = Application(company=application.company, role=application.role, status=application.status,
                      job_url=application.job_url, notes=application.notes,
                      applied_at=datetime.now(UTC) if application.status != "saved" else None,
                      user_id=user.id)

    try:
        session.add(new_application)
        await session.commit()
        await session.refresh(new_application)

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    return new_application

# Returns total number of rows in Application table, as well as number of rows for each type of status
async def get_application_stats(user: User, db: AsyncSession):
    statement = select(func.count()).select_from(Application).where(Application.user_id == user.id)

    try:
        total = (await db.exec(statement)).one()
        saved = (await db.exec(statement.where(Application.status == "saved"))).one()
        applied = (await db.exec(statement.where(Application.status == "applied"))).one()
        interview = (await db.exec(statement.where(Application.status == "interview"))).one()
        offer = (await db.exec(statement.where(Application.status == "offer"))).one()
        rejected = (await db.exec(statement.where(Application.status == "rejected"))).one()

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

# Get a specific instance from Application db table by its id
async def get_application(user: User,
                          application_id: int,
                          db: AsyncSession) -> Application:
    try:
        statement = select(Application).where(Application.id == application_id,
                                              Application.user_id == user.id)
        result = await db.exec(statement)
        application = result.one_or_none()

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    return application

# Delete a specific instance from Application db table using its id
async def delete_application(application_id: int, session: AsyncSession):
    try:
        application = await session.get(Application, application_id)

        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        await session.delete(application)
        await session.commit()

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

# Update the attributes of a specific instance in Application db table using its id
async def update_application(application_id: int, update: ApplicationUpdate,
                             session: AsyncSession) -> Application:
    application = await session.get(Application, application_id)

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