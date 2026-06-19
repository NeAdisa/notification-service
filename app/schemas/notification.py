from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.notification import NotificationPriority, NotificationStatus


class NotificationCreate(BaseModel):
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=500)
    send_at: datetime
    priority: NotificationPriority

    @field_validator("send_at")
    @classmethod
    def send_at_must_not_be_in_past(cls, value: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        comparable_value = value
        if comparable_value.tzinfo is None:
            comparable_value = comparable_value.replace(tzinfo=timezone.utc)
        if comparable_value < now:
            raise ValueError("send_at must not be in the past")
        return value


class NotificationRead(BaseModel):
    id: int
    email: EmailStr
    message: str
    send_at: datetime
    priority: NotificationPriority
    status: NotificationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
