from fastapi import status, Path, Depends, Query, APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, Literal
from app.database import get_session
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.services import applications as application_service

router = APIRouter(prefix="/applications", tags=["applications"],)

# Return all applications. We could use list[Application] itself as the response_model, but I am not sure about it yet
@router.get("/", response_model=list[ApplicationRead])
async def get_applications(status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None,
                           sort_by: Literal["applied_at", "created_at", "updated_at"] | None = None,
                           order: Literal["asc", "desc"] = "asc",
                           page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                           session: AsyncSession = Depends(get_session)) -> list[ApplicationRead]:
    return await application_service.get_applications(session, status, sort_by, order, page, page_size)

# Create an application. applied_at and updated_at is set to current time unless status is saved, can edit later
# using patch endpoint, but we could also allow setting them in this post endpoint. Not sure yet if I should
# change the implementation to do that yet.
@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_applications(application: ApplicationCreate,
                              session: AsyncSession = Depends(get_session)) -> ApplicationRead:
    return await application_service.create_application(application, session)

# Get statistics about the total number of applications and number of applications with each status type.
# Inefficient due to multiple queries, more efficient way to do it that I will defer for now because
# of SQLModel giving unexpected behaviour
@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    return await application_service.get_application_stats(session)

# Get a specific application by id
@router.get("/{id}", response_model=ApplicationRead)
async def get_application(id: Annotated[int, Path(ge=1)],
                          session: AsyncSession = Depends(get_session)) -> ApplicationRead:
    return await application_service.get_application(id, session)


# Delete a specific application by id
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(id: Annotated[int, Path(ge=1)], session: AsyncSession = Depends(get_session)):
    await application_service.delete_application(id, session)

# Update a specific application's details (i.e. a patch) by id
@router.patch("/{id}", response_model=ApplicationRead)
async def update_application(id: Annotated[int, Path(ge=1)], update: ApplicationUpdate,
                             session: AsyncSession = Depends(get_session)) -> ApplicationRead:
    return await application_service.update_application(id, update, session)
