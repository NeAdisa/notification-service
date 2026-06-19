from fastapi import HTTPException, status

from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationStatus,
)
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationCreate


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def create(self, payload: NotificationCreate) -> Notification:
        return await self.repository.create(payload)

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        priority: NotificationPriority | None = None,
    ) -> list[Notification]:
        return await self.repository.list(
            limit=limit,
            offset=offset,
            priority=priority,
        )

    async def delete(self, notification_id: int) -> None:
        notification = await self.repository.get_by_id(notification_id)
        if notification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        if notification.status != NotificationStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only scheduled notifications can be deleted",
            )

        await self.repository.delete(notification)
