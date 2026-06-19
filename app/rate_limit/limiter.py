from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.rate_limit.redis import get_redis_client

RATE_LIMIT_WINDOW_SECONDS = 60


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()

    if request.client is None:
        return "unknown"

    return request.client.host


async def limit_notifications_by_ip(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    client_ip = get_client_ip(request)
    key = f"rate_limit:notifications:create:{client_ip}"

    current_count = await redis.incr(key)
    if current_count == 1:
        await redis.expire(key, RATE_LIMIT_WINDOW_SECONDS)

    if current_count > settings.rate_limit_max:
        ttl = await redis.ttl(key)
        retry_after = max(ttl, 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
