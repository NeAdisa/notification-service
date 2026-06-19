from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.notifications import router as notifications_router
from app.rate_limit.redis import redis_client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    yield
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
