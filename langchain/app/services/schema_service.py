import time
from collections.abc import Callable
from threading import Lock


class SchemaService:
    """Caches a backend's schema text (rendered by its repository) with a TTL."""

    def __init__(self, describe: Callable[[], str], ttl_seconds: int):
        self._describe = describe
        self._ttl = ttl_seconds
        self._text = ""
        self._ts = 0.0
        self._lock = Lock()

    def get(self, force: bool = False) -> str:
        with self._lock:
            fresh = (time.time() - self._ts) < self._ttl
            if self._text and fresh and not force:
                return self._text
            self._text = self._describe()
            self._ts = time.time()
            return self._text
