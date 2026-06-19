from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.rate_limit.limiter import limit_notifications_by_ip


class FakeRedis:
    def __init__(self) -> None:
        self.count = 0
        self.expire_calls: list[tuple[str, int]] = []

    async def incr(self, key: str) -> int:
        self.count += 1
        return self.count

    async def expire(self, key: str, seconds: int) -> None:
        self.expire_calls.append((key, seconds))

    async def ttl(self, key: str) -> int:
        return 42


def make_request(host: str = "127.0.0.1") -> SimpleNamespace:
    return SimpleNamespace(headers={}, client=SimpleNamespace(host=host))


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_under_limit() -> None:
    redis = FakeRedis()
    settings = Settings(RATE_LIMIT_MAX=2)

    await limit_notifications_by_ip(make_request(), redis, settings)
    await limit_notifications_by_ip(make_request(), redis, settings)

    assert redis.count == 2
    assert redis.expire_calls == [("rate_limit:notifications:create:127.0.0.1", 60)]


@pytest.mark.asyncio
async def test_rate_limiter_blocks_requests_over_limit() -> None:
    redis = FakeRedis()
    settings = Settings(RATE_LIMIT_MAX=1)

    await limit_notifications_by_ip(make_request(), redis, settings)

    with pytest.raises(HTTPException) as exc_info:
        await limit_notifications_by_ip(make_request(), redis, settings)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Rate limit exceeded"
    assert exc_info.value.headers == {"Retry-After": "42"}
