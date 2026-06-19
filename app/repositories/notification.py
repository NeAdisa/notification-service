from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationStatus,
)
from app.schemas.notification import NotificationCreate


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payload: NotificationCreate) -> Notification:
        notification = Notification(
            email=str(payload.email),
            message=payload.message,
            send_at=payload.send_at,
            priority=payload.priority,
            status=NotificationStatus.SCHEDULED,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        priority: NotificationPriority | None = None,
    ) -> list[Notification]:
        query: Select[tuple[Notification]] = select(Notification).order_by(
            Notification.send_at,
            Notification.id,
        )
        if priority is not None:
            query = query.where(Notification.priority == priority)

        result = await self.session.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return await self.session.get(Notification, notification_id)

    async def delete(self, notification: Notification) -> None:
        await self.session.delete(notification)
        await self.session.commit()
