from fastapi import status, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func, case
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


# Returns total number of applications for a user, as well as number of applications of each type of status
async def get_application_stats(user: User, db: AsyncSession):
    statement = (
        select(
            func.count().label("total"),
            func.count(
                case((Application.status == "saved", 1))
            ).label("saved"),
            func.count(
                case((Application.status == "applied", 1))
            ).label("applied"),
            func.count(
                case((Application.status == "interview", 1))
            ).label("interview"),
            func.count(
                case((Application.status == "offer", 1))
            ).label("offer"),
            func.count(
                case((Application.status == "rejected", 1))
            ).label("rejected"),
        )
        .select_from(Application)
        .where(Application.user_id == user.id)
    )

    try:
        total, saved, applied, interview, offer, rejected = (
            await db.exec(statement)
        ).one()

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    return {
        "total": total,
        "saved": saved,
        "applied": applied,
        "interview": interview,
        "offer": offer,
        "rejected": rejected,
    }



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
async def delete_application(user: User, application_id: int, db: AsyncSession):
    statement = select(Application).where(Application.id == application_id,
                                        Application.user_id == user.id)
    try:
        application = (await db.exec(statement)).one_or_none()

        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Application not found")
        
        await db.delete(application)
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")



# Update the attributes of a specific instance in Application db table using its id
async def update_application(user: User,
                             application_id: int, update: ApplicationUpdate,
                             db: AsyncSession) -> Application:
    update_data = update.model_dump(exclude_unset=True)

    if update_data.get("status") == "saved":
        update_data["applied_at"] = None

    update_data["updated_at"] = datetime.now(UTC)

    statement = select(Application).where(Application.id == application_id,
                                        Application.user_id == user.id)

    try:
        application = (await db.exec(statement)).one_or_none()

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.sqlmodel_update(update_data)

    try:
        db.add(application)
        await db.commit()
        await db.refresh(application)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    return application