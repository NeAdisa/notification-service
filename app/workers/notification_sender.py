import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationSender:
    async def send(self, notification: Notification) -> None:
        logger.info(
            "Sending notification %s to %s",
            notification.id,
            notification.email,
        )
        await asyncio.sleep(0)


async def process_due_notifications() -> None:
    settings = get_settings()
    sender = NotificationSender()

    async with AsyncSessionLocal() as session:
        repository = NotificationRepository(session)
        notifications = await repository.get_due_for_sending(
            now=datetime.now(timezone.utc),
            limit=settings.sender_batch_size,
        )

        for notification in notifications:
            attempted_at = datetime.now(timezone.utc)
            await repository.mark_processing(
                notification,
                attempted_at=attempted_at,
            )

            try:
                await sender.send(notification)
            except Exception as exc:
                logger.exception(
                    "Failed to send notification %s",
                    notification.id,
                )
                await repository.mark_send_failed(notification, error=str(exc))
            else:
                await repository.mark_sent(
                    notification,
                    sent_at=datetime.now(timezone.utc),
                )


async def run_notification_sender_loop() -> None:
    settings = get_settings()

    while True:
        try:
            await process_due_notifications()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Notification sender loop iteration failed")

        await asyncio.sleep(settings.sender_interval_seconds)
