import time
from typing import Dict, Optional, Tuple


class MemoryTTLStore:
    """Tiny in-process TTL cache used when Redis is disabled or unreachable."""

    def __init__(self, max_items: int = 1000):
        self._data: Dict[str, Tuple[float, str]] = {}
        self._max_items = max_items

    def get(self, key: str) -> Optional[str]:
        item = self._data.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if len(self._data) >= self._max_items:
            now = time.time()
            self._data = {k: v for k, v in self._data.items() if v[0] >= now}
            if len(self._data) >= self._max_items:
                self._data.pop(next(iter(self._data)))
        self._data[key] = (time.time() + ttl_seconds, value)

    def clear(self) -> None:
        self._data.clear()


memory_store = MemoryTTLStore()
