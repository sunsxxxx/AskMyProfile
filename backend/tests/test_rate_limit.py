import asyncio

import fakeredis.aioredis
import pytest

from app.core.rate_limit import SlidingWindowRateLimiter


@pytest.fixture
def redis_client():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def limiter(redis_client):
    return SlidingWindowRateLimiter(
        redis_client, max_requests=5, window_seconds=60, key_ttl_seconds=90
    )


@pytest.mark.asyncio
async def test_first_five_allowed_and_sixth_rejected(limiter):
    results = [await limiter.check("203.0.113.10", now=100 + i / 1000) for i in range(6)]
    assert [item.allowed for item in results] == [True, True, True, True, True, False]
    assert 1 <= results[-1].retry_after <= 60


@pytest.mark.asyncio
async def test_window_recovers(limiter):
    for index in range(5):
        assert (await limiter.check("203.0.113.11", now=10 + index / 100)).allowed
    assert not (await limiter.check("203.0.113.11", now=20)).allowed
    assert (await limiter.check("203.0.113.11", now=71)).allowed


@pytest.mark.asyncio
async def test_two_ips_are_independent(limiter):
    for index in range(5):
        assert (await limiter.check("203.0.113.12", now=30 + index / 100)).allowed
    assert not (await limiter.check("203.0.113.12", now=31)).allowed
    assert (await limiter.check("203.0.113.13", now=31)).allowed


@pytest.mark.asyncio
async def test_concurrent_requests_allow_at_most_five(limiter):
    results = await asyncio.gather(
        *(limiter.check("203.0.113.14", now=50) for _ in range(20))
    )
    assert sum(item.allowed for item in results) == 5

