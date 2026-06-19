from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.notification import NotificationPriority, NotificationStatus


class NotificationCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Recipient email address.",
        examples=["student@example.com"],
    )
    message: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Notification body, from 10 to 500 characters.",
        examples=["Your assignment deadline is tomorrow at 18:00."],
    )
    send_at: datetime = Field(
        ...,
        description="Date and time when the notification should be sent.",
        examples=["2030-06-19T12:00:00Z"],
    )
    priority: NotificationPriority = Field(
        ...,
        description="Notification priority.",
        examples=[NotificationPriority.HIGH],
    )
    max_attempts: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description=(
            "Optional retry limit for this notification. If omitted, the "
            "application default is used."
        ),
        examples=[3],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "student@example.com",
                    "message": "Your assignment deadline is tomorrow at 18:00.",
                    "send_at": "2030-06-19T12:00:00Z",
                    "priority": "high",
                    "max_attempts": 3,
                }
            ]
        }
    )

    @field_validator("send_at")
    @classmethod
    def send_at_must_not_be_in_past(cls, value: datetime) -> datetime:
        now = datetime.now(UTC)
        comparable_value = value
        if comparable_value.tzinfo is None:
            comparable_value = comparable_value.replace(tzinfo=UTC)
        if comparable_value < now:
            raise ValueError("send_at must not be in the past")
        return value


class NotificationRead(BaseModel):
    id: int = Field(..., description="Unique notification identifier.", examples=[1])
    email: EmailStr = Field(
        ...,
        description="Recipient email address.",
        examples=["student@example.com"],
    )
    message: str = Field(
        ...,
        description="Notification body.",
        examples=["Your assignment deadline is tomorrow at 18:00."],
    )
    send_at: datetime = Field(
        ...,
        description="Scheduled sending time.",
        examples=["2030-06-19T12:00:00Z"],
    )
    priority: NotificationPriority = Field(
        ...,
        description="Notification priority.",
        examples=[NotificationPriority.HIGH],
    )
    status: NotificationStatus = Field(
        ...,
        description="Current delivery status.",
        examples=[NotificationStatus.SCHEDULED],
    )
    attempt_count: int = Field(
        ...,
        description="Number of delivery attempts already made.",
        examples=[0],
    )
    max_attempts: int = Field(
        ...,
        description="Maximum delivery attempts before marking as failed.",
        examples=[3],
    )
    last_attempt_at: datetime | None = Field(
        default=None,
        description="Timestamp of the latest delivery attempt.",
        examples=[None],
    )
    sent_at: datetime | None = Field(
        default=None,
        description="Timestamp when the notification was successfully sent.",
        examples=[None],
    )
    last_error: str | None = Field(
        default=None,
        description="Latest delivery error, if any.",
        examples=[None],
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp.",
        examples=["2030-06-18T09:30:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp.",
        examples=["2030-06-18T09:30:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "student@example.com",
                    "message": "Your assignment deadline is tomorrow at 18:00.",
                    "send_at": "2030-06-19T12:00:00Z",
                    "priority": "high",
                    "status": "scheduled",
                    "attempt_count": 0,
                    "max_attempts": 3,
                    "last_attempt_at": None,
                    "sent_at": None,
                    "last_error": None,
                    "created_at": "2030-06-18T09:30:00Z",
                    "updated_at": "2030-06-18T09:30:00Z",
                }
            ]
        },
    )
