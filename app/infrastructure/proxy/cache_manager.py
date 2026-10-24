import json
import hashlib
from typing import Dict, Any, Optional

import structlog

from app.core.config import settings
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.cache.memory_store import memory_store

logger = structlog.get_logger("cache_manager")


def _cache_key(path: str, body: Dict[str, Any]) -> str:
    key_raw = f"{path}:{json.dumps(body, sort_keys=True)}"
    return f"gateway_cache:{hashlib.sha256(key_raw.encode()).hexdigest()}"


class CacheManager:
    @staticmethod
    async def get_cached_response(path: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cache_key = _cache_key(path, body)
        if not settings.USE_REDIS:
            data = memory_store.get(cache_key)
        else:
            try:
                data = await redis_client.get(cache_key)
            except Exception as e:
                # The cache is an optimisation; never fail a request over it.
                logger.warning("Cache read failed", error=str(e))
                return None
        return json.loads(data) if data else None

    @staticmethod
    async def set_cached_response(path: str, body: Dict[str, Any], response: Dict[str, Any], ttl_seconds: int = 60):
        cache_key = _cache_key(path, body)
        payload = json.dumps(response)
        if not settings.USE_REDIS:
            memory_store.set(cache_key, payload, ttl_seconds)
            return
        try:
            await redis_client.setex(cache_key, ttl_seconds, payload)
        except Exception as e:
            logger.warning("Cache write failed", error=str(e))
