from __future__ import annotations

import hashlib
import math
import secrets
import time
from dataclasses import dataclass

from redis.asyncio import Redis


SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])
local member = ARGV[5]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = window
    if oldest[2] then
        retry_after = math.max(1, math.ceil(window - (now - tonumber(oldest[2]))))
    end
    redis.call('EXPIRE', key, ttl)
    return {0, retry_after, count}
end

redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, ttl)
return {1, 0, count + 1}
"""


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after: int
    count: int


class SlidingWindowRateLimiter:
    def __init__(
        self,
        redis: Redis,
        *,
        max_requests: int = 5,
        window_seconds: int = 60,
        key_ttl_seconds: int = 90,
        prefix: str = "portfolio:rate_limit",
    ) -> None:
        if key_ttl_seconds <= window_seconds:
            raise ValueError("Rate-limit key TTL must be greater than its window")
        self.redis = redis
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_ttl_seconds = key_ttl_seconds
        self.prefix = prefix

    async def check(self, client_ip: str, *, now: float | None = None) -> RateLimitResult:
        timestamp = time.time() if now is None else now
        key_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:32]
        member = f"{timestamp:.6f}:{secrets.token_hex(8)}"
        raw = await self.redis.eval(
            SLIDING_WINDOW_LUA,
            1,
            f"{self.prefix}:{{{key_hash}}}",
            timestamp,
            self.window_seconds,
            self.max_requests,
            self.key_ttl_seconds,
            member,
        )
        return RateLimitResult(bool(int(raw[0])), int(math.ceil(float(raw[1]))), int(raw[2]))

