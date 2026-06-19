from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="Human-readable error message.",
        examples=["Notification not found"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Notification not found"},
                {"detail": "Rate limit exceeded"},
            ]
        }
    )
