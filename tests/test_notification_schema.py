from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.notification import NotificationPriority
from app.schemas.notification import NotificationCreate


def valid_notification_payload() -> dict[str, object]:
    return {
        "email": "student@example.com",
        "message": "Your assignment deadline is tomorrow.",
        "send_at": datetime.now(UTC) + timedelta(hours=1),
        "priority": NotificationPriority.HIGH,
    }


def test_notification_create_accepts_valid_payload() -> None:
    schema = NotificationCreate(**valid_notification_payload())

    assert schema.email == "student@example.com"
    assert schema.priority == NotificationPriority.HIGH


def test_notification_create_rejects_short_message() -> None:
    payload = valid_notification_payload()
    payload["message"] = "Too short"

    with pytest.raises(ValidationError):
        NotificationCreate(**payload)


def test_notification_create_rejects_past_send_at() -> None:
    payload = valid_notification_payload()
    payload["send_at"] = datetime.now(UTC) - timedelta(minutes=1)

    with pytest.raises(ValidationError, match="send_at must not be in the past"):
        NotificationCreate(**payload)
