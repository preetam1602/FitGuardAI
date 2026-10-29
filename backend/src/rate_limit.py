"""
In-memory sliding-window rate limiting for the auth endpoints.

Counters live in this process, so limits apply per uvicorn worker. If the API is ever run
with several workers or instances, move the counters to a shared store such as Redis.
"""

import math
import time
from collections import deque
from typing import Callable, Deque, Dict


class SlidingWindowLimiter:
    """Allows at most `max_events` per key within any `window_s`-second window."""

    def __init__(self, max_events: int, window_s: float, max_keys: int = 100_000,
                 clock: Callable[[], float] = time.monotonic):
        self.max_events = max_events
        self.window_s = window_s
        self.max_keys = max_keys
        self._clock = clock
        # Only the newest `max_events` timestamps matter, so each deque is bounded
        self._events: Dict[str, Deque[float]] = {}

    def _live(self, key: str, now: float):
        """The key's timestamps still inside the window, dropping the key once it has none."""
        q = self._events.get(key)
        if q is None:
            return None
        while q and q[0] <= now - self.window_s:
            q.popleft()
        if not q:
            del self._events[key]
            return None
        return q

    def retry_after(self, key: str) -> int:
        """Seconds until `key` may act again; 0 if it is under the limit."""
        now = self._clock()
        q = self._live(key, now)
        if q is None or len(q) < self.max_events:
            return 0
        return max(1, math.ceil(q[0] + self.window_s - now))

    def hit(self, key: str) -> None:
        now = self._clock()
        if key not in self._events and len(self._events) >= self.max_keys:
            self._evict(now)
        self._events.setdefault(key, deque(maxlen=self.max_events)).append(now)

    def undo(self, key: str) -> None:
        """Forget the key's most recent event (e.g. an attempt that turned out to succeed)."""
        q = self._events.get(key)
        if q:
            q.pop()
            if not q:
                del self._events[key]

    def reset(self, key: str) -> None:
        self._events.pop(key, None)

    def _evict(self, now: float) -> None:
        for key in list(self._events):
            self._live(key, now)
        # Still full (e.g. a flood of distinct keys): drop the oldest-inserted keys to bound memory
        while len(self._events) >= self.max_keys:
            del self._events[next(iter(self._events))]
