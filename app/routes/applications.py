from fastapi import status, Path, Depends, Query, APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, Literal
from app.database import get_session
from app.models import User
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.services import applications as application_service
from app.services import auth as auth_service


router = APIRouter(prefix="/applications", tags=["applications"],)


# Return all applications.
@router.get("/", response_model=list[ApplicationRead])
async def get_applications(user: Annotated[User, Depends(auth_service.get_current_user)],
                           db: Annotated[AsyncSession, Depends(get_session)],
                           status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None,
                           sort_by: Literal["applied_at", "created_at", "updated_at"] | None = None,
                           order: Literal["asc", "desc"] = "asc",
                           page: int = Query(1, ge=1),
                           page_size: int = Query(20, ge=1, le=100)) -> list[ApplicationRead]:
    return await application_service.get_applications(user=user, db=db,
                                                      app_status=status, sort_by=sort_by,
                                                      order=order, page=page, page_size=page_size)



# Create an application.
@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(user: Annotated[User, Depends(auth_service.get_current_user)],
                             application: ApplicationCreate,
                              db: Annotated[AsyncSession, Depends(get_session)]) -> ApplicationRead:
    return await application_service.create_application(user, application, db)



# Get statistics about the total number of applications and number of applications with each status type.
@router.get("/stats")
async def get_stats(user: Annotated[User, Depends(auth_service.get_current_user)],
                    db: Annotated[AsyncSession, Depends(get_session)]):
    return await application_service.get_application_stats(user, db)



# Get a specific application by id
@router.get("/{id}", response_model=ApplicationRead)
async def get_application(user: Annotated[User, Depends(auth_service.get_current_user)],
                          id: Annotated[int, Path(ge=1)],
                          db: Annotated[AsyncSession, Depends(get_session)]) -> ApplicationRead:
    return await application_service.get_application(user, id, db)



# Delete a specific application by id
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(user: Annotated[User, Depends(auth_service.get_current_user)],
                             id: Annotated[int, Path(ge=1)], db: Annotated[AsyncSession, Depends(get_session)]):
    await application_service.delete_application(user, id, db)



# Update a specific application's details (i.e. a patch) by id
@router.patch("/{id}", response_model=ApplicationRead)
async def update_application(user: Annotated[User, Depends(auth_service.get_current_user)],
                             id: Annotated[int, Path(ge=1)], update: ApplicationUpdate,
                             db: Annotated[AsyncSession, Depends(get_session)]) -> ApplicationRead:
    return await application_service.update_application(user, id, update, db)
