import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.api.routes.notifications import router as notifications_router
from app.rate_limit.redis import redis_client
from app.workers.notification_sender import run_notification_sender_loop


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    sender_task = asyncio.create_task(run_notification_sender_loop())
    try:
        yield
    finally:
        sender_task.cancel()
        with suppress(asyncio.CancelledError):
            await sender_task
    await redis_client.aclose()


app = FastAPI(
    title="Notification Service",
    version="0.1.0",
    description="REST API for scheduling notifications.",
    lifespan=lifespan,
)

app.include_router(notifications_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
