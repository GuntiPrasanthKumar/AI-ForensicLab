import hashlib
import time
import threading
from typing import Dict, Any, Optional

class CacheManager:
    """
    Thread-safe in-memory TTL cache with hash-based lookup.
    Prevents duplicate API calls for identical requests.
    """
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 500):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _generate_key(self, prefix: str, content: Any) -> str:
        if isinstance(content, str):
            data = content.strip().encode('utf-8')
        elif isinstance(content, bytes):
            data = content
        else:
            data = str(content).encode('utf-8')
        
        hasher = hashlib.sha256(data)
        return f"{prefix}:{hasher.hexdigest()}"

    def get(self, prefix: str, content: Any) -> Optional[Dict[str, Any]]:
        key = self._generate_key(prefix, content)
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() - entry["timestamp"] > self.ttl:
                del self._cache[key]
                return None
            
            # Return copy with cache hit flag
            result = dict(entry["data"])
            result["is_cached"] = True
            return result

    def set(self, prefix: str, content: Any, data: Dict[str, Any]) -> None:
        key = self._generate_key(prefix, content)
        with self._lock:
            # Evict oldest entries if cache exceeds max capacity
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
                del self._cache[oldest_key]
                
            clean_data = dict(data)
            clean_data.pop("is_cached", None)
            
            self._cache[key] = {
                "timestamp": time.time(),
                "data": clean_data
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

# Global singleton cache instance
global_cache = CacheManager()
