from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, case, select
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

    async def create(
        self,
        payload: NotificationCreate,
        *,
        max_attempts: int,
    ) -> Notification:
        notification = Notification(
            email=str(payload.email),
            message=payload.message,
            send_at=payload.send_at,
            priority=payload.priority,
            status=NotificationStatus.SCHEDULED,
            max_attempts=max_attempts,
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

    async def get_due_for_sending(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[Notification]:
        priority_order = case(
            (Notification.priority == NotificationPriority.HIGH, 1),
            (Notification.priority == NotificationPriority.MEDIUM, 2),
            (Notification.priority == NotificationPriority.LOW, 3),
            else_=4,
        )
        query = (
            select(Notification)
            .where(Notification.status == NotificationStatus.SCHEDULED)
            .where(Notification.send_at <= now)
            .where(Notification.attempt_count < Notification.max_attempts)
            .order_by(priority_order, Notification.send_at, Notification.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_processing(
        self,
        notification: Notification,
        *,
        attempted_at: datetime,
    ) -> None:
        notification.status = NotificationStatus.PROCESSING
        notification.attempt_count += 1
        notification.last_attempt_at = attempted_at
        notification.last_error = None
        await self.session.commit()
        await self.session.refresh(notification)

    async def mark_sent(
        self,
        notification: Notification,
        *,
        sent_at: datetime,
    ) -> None:
        notification.status = NotificationStatus.SENT
        notification.sent_at = sent_at
        notification.last_error = None
        await self.session.commit()

    async def mark_send_failed(
        self,
        notification: Notification,
        *,
        error: str,
    ) -> None:
        notification.last_error = error[:500]
        if notification.attempt_count >= notification.max_attempts:
            notification.status = NotificationStatus.FAILED
        else:
            notification.status = NotificationStatus.SCHEDULED
        await self.session.commit()
