from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.notification import NotificationPriority
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationService:
    repository = NotificationRepository(session)
    return NotificationService(repository)


@router.post(
    "",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    payload: NotificationCreate,
    service: Annotated[NotificationService, Depends(get_notification_service)],
):
    return await service.create(payload)


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    priority: NotificationPriority | None = None,
):
    return await service.list(limit=limit, offset=offset, priority=priority)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_notification(
    notification_id: int,
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> Response:
    await service.delete(notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
