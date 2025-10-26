# app/utils/ai_cache.py
import time
from typing import Any, Dict, Tuple

class _AICache:
    def __init__(self):
        self._store: Dict[Tuple, Tuple[float, Any, float]] = {}
        # key -> (ts_created, value, ttl_seconds)

    def get(self, key: Tuple) -> Any:
        item = self._store.get(key)
        if not item:
            return None
        ts, val, ttl = item
        if ttl > 0 and (time.time() - ts) > ttl:
            # expired
            try:
                del self._store[key]
            except Exception:
                pass
            return None
        return val

    def set(self, key: Tuple, value: Any, ttl_seconds: float = 86400) -> None:
        self._store[key] = (time.time(), value, ttl_seconds)

ai_cache = _AICache()
