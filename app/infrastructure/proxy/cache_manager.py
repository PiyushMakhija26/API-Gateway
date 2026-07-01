import json
import hashlib
from typing import Dict, Any, Optional
from app.infrastructure.cache.redis_client import redis_client

class CacheManager:
    @staticmethod
    async def get_cached_response(path: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key_raw = f"{path}:{json.dumps(body, sort_keys=True)}"
        cache_key = f"gateway_cache:{hashlib.sha256(key_raw.encode()).hexdigest()}"
        
        data = await redis_client.get(cache_key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    async def set_cached_response(path: str, body: Dict[str, Any], response: Dict[str, Any], ttl_seconds: int = 60):
        key_raw = f"{path}:{json.dumps(body, sort_keys=True)}"
        cache_key = f"gateway_cache:{hashlib.sha256(key_raw.encode()).hexdigest()}"
        
        await redis_client.setex(cache_key, ttl_seconds, json.dumps(response))
