import time
from typing import Dict, Tuple

import structlog

from app.core.config import settings
from app.infrastructure.cache.redis_client import redis_client

logger = structlog.get_logger("rate_limiter")

# Atomic token bucket: refill, then take one token if available.
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

if not tokens then
    tokens = capacity
    last_refill = current_time
end

local time_passed = current_time - last_refill
local new_tokens = time_passed * refill_rate
tokens = math.min(capacity, tokens + new_tokens)

local allowed = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
end
redis.call('HMSET', key, 'tokens', tokens, 'last_refill', current_time)
redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 10)
return allowed
"""


class RedisTokenBucketRateLimiter:
    def __init__(self, key_prefix: str, capacity: int, refill_rate: float):
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_rate = refill_rate # tokens per second
        self._local_buckets: Dict[str, Tuple[float, float]] = {}

    async def is_allowed(self, identifier: str) -> bool:
        key = f"rate_limit:{self.key_prefix}:{identifier}"
        current_time = time.time()

        if not settings.USE_REDIS:
            return self._allow_local(key, current_time)

        try:
            result = await redis_client.eval(
                TOKEN_BUCKET_LUA, 1, key, self.capacity, self.refill_rate, current_time
            )
        except Exception as e:
            # Fail open on a Redis outage but keep a local safety net.
            logger.warning("Rate limiter Redis call failed, using local bucket", error=str(e))
            return self._allow_local(key, current_time)
        return result == 1

    def _allow_local(self, key: str, now: float) -> bool:
        tokens, last_refill = self._local_buckets.get(key, (float(self.capacity), now))
        tokens = min(self.capacity, tokens + (now - last_refill) * self.refill_rate)
        allowed = tokens >= 1
        if allowed:
            tokens -= 1
        self._local_buckets[key] = (tokens, now)
        return allowed
