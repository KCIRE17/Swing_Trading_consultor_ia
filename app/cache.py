import threading
import time

DEFAULT_TTL = 3600


class TTLCache:
    def __init__(self, ttl=DEFAULT_TTL, maxsize=128):
        self._ttl = ttl
        self._maxsize = maxsize
        self._data = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            stored_at, value = item
            if time.monotonic() - stored_at > self._ttl:
                del self._data[key]
                return None
            return value

    def set(self, key, value, ttl=None):
        with self._lock:
            self._data[key] = (time.monotonic(), value)
            if len(self._data) > self._maxsize:
                oldest = min(self._data, key=lambda k: self._data[k][0])
                del self._data[oldest]

    def clear(self):
        with self._lock:
            self._data.clear()


DATA_CACHE = TTLCache()