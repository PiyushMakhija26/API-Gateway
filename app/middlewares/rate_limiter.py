import time
from app.infrastructure.cache.redis_client import redis_client

class RedisTokenBucketRateLimiter:
    def __init__(self, key_prefix: str, capacity: int, refill_rate: float):
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_rate = refill_rate # tokens per second

    async def is_allowed(self, identifier: str) -> bool:
        key = f"rate_limit:{self.key_prefix}:{identifier}"
        current_time = time.time()
        
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.hgetall(key)
            result = await pipe.execute()
            data = result[0]
            
            if not data:
                tokens = self.capacity - 1
                last_refill = current_time
                pipe.hset(key, mapping={"tokens": tokens, "last_refill": last_refill})
                pipe.expire(key, int(self.capacity / self.refill_rate) + 10)
                await pipe.execute()
                return True
                
            tokens = float(data.get('tokens', self.capacity))
            last_refill = float(data.get('last_refill', current_time))
            
            time_passed = current_time - last_refill
            new_tokens = time_passed * self.refill_rate
            
            tokens = min(self.capacity, tokens + new_tokens)
            
            if tokens >= 1:
                tokens -= 1
                pipe.hset(key, mapping={"tokens": tokens, "last_refill": current_time})
                await pipe.execute()
                return True
            else:
                return False
