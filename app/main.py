from fastapi import FastAPI

from app.api.routes.notifications import router as notifications_router

app = FastAPI(
    title="Notification Service",
    version="0.1.0",
    description="REST API for scheduling notifications.",
)

app.include_router(notifications_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
