from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.notification import NotificationStatus
from app.services.notification import NotificationService


class FakeRepository:
    def __init__(self, notification: SimpleNamespace | None) -> None:
        self.notification = notification
        self.deleted_notification: SimpleNamespace | None = None

    async def get_by_id(self, notification_id: int) -> SimpleNamespace | None:
        return self.notification

    async def delete(self, notification: SimpleNamespace) -> None:
        self.deleted_notification = notification


@pytest.mark.asyncio
async def test_delete_removes_scheduled_notification() -> None:
    notification = SimpleNamespace(status=NotificationStatus.SCHEDULED)
    repository = FakeRepository(notification)
    service = NotificationService(repository)

    await service.delete(1)

    assert repository.deleted_notification is notification


@pytest.mark.asyncio
async def test_delete_rejects_sent_notification() -> None:
    repository = FakeRepository(SimpleNamespace(status=NotificationStatus.SENT))
    service = NotificationService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete(1)

    assert exc_info.value.status_code == 409
    assert repository.deleted_notification is None
