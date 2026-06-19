from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.notification import NotificationPriority
from app.rate_limit.limiter import limit_notifications_by_ip
from app.repositories.notification import NotificationRepository
from app.schemas.common import ErrorResponse
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

VALIDATION_ERROR_RESPONSE = {
    "description": "Request validation failed.",
    "content": {
        "application/json": {
            "example": {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "send_at"],
                        "msg": "Value error, send_at must not be in the past",
                        "input": "2020-01-01T00:00:00Z",
                    }
                ]
            }
        }
    },
}


def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationService:
    repository = NotificationRepository(session)
    return NotificationService(repository)


@router.post(
    "",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a notification",
    description=(
        "Creates a scheduled notification for a recipient email. The endpoint "
        "is rate-limited per client IP and accepts only future send times."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "description": "Notification scheduled successfully.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: VALIDATION_ERROR_RESPONSE,
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded for the client IP.",
            "headers": {
                "Retry-After": {
                    "description": "Seconds until another request is allowed.",
                    "schema": {"type": "integer", "example": 42},
                }
            },
            "content": {
                "application/json": {"example": {"detail": "Rate limit exceeded"}}
            },
        },
    },
)
async def create_notification(
    payload: NotificationCreate,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    _: Annotated[None, Depends(limit_notifications_by_ip)],
):
    return await service.create(payload)


@router.get(
    "",
    response_model=list[NotificationRead],
    summary="List notifications",
    description=(
        "Returns scheduled and processed notifications ordered by send time. "
        "Results can be paginated and filtered by priority."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Notifications returned successfully.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: VALIDATION_ERROR_RESPONSE,
    },
)
async def list_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of notifications to return.",
            examples=[20],
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of notifications to skip before returning data.",
            examples=[0],
        ),
    ] = 0,
    priority: Annotated[
        NotificationPriority | None,
        Query(
            description="Optional priority filter.",
            examples=[NotificationPriority.HIGH],
        ),
    ] = None,
):
    return await service.list(limit=limit, offset=offset, priority=priority)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a scheduled notification",
    description=(
        "Deletes a notification only while it is still scheduled. Sent, failed, "
        "processing, or cancelled notifications cannot be deleted."
    ),
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Scheduled notification deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Notification with the given ID does not exist.",
            "content": {
                "application/json": {"example": {"detail": "Notification not found"}}
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Notification exists but is not scheduled anymore.",
            "content": {
                "application/json": {
                    "example": {"detail": "Only scheduled notifications can be deleted"}
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: VALIDATION_ERROR_RESPONSE,
    },
)
async def delete_notification(
    notification_id: Annotated[
        int,
        Path(
            ge=1,
            description="Unique notification identifier.",
            examples=[1],
        ),
    ],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> Response:
    await service.delete(notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
