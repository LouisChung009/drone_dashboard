"""Simple per-source rate limiting utilities."""

from __future__ import annotations

import time
from threading import Lock
from typing import Dict


class RateLimiter:
    """One request per `interval` seconds for each key."""

    def __init__(self, interval_seconds: float = 1.0):
        self.interval = interval_seconds
        self._last_run: Dict[str, float] = {}
        self._lock = Lock()

    def wait(self, key: str) -> None:
        """Block the caller until the key respects the configured rate."""

        with self._lock:
            now = time.monotonic()
            last = self._last_run.get(key)
            if last is None:
                self._last_run[key] = now
                return

            delta = now - last
            if delta < self.interval:
                time.sleep(self.interval - delta)
            self._last_run[key] = time.monotonic()
