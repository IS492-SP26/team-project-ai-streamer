"""Very small synchronous rate limiter (token bucket) for demo use.

Not intended as production-grade; demonstrates how to throttle downstream calls.
"""
import time
from threading import Lock


class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        """rate: tokens per second, capacity: max tokens"""
        self.rate = float(rate)
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = Lock()

    def consume(self, tokens: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_for_token(self, tokens: float = 1.0):
        while True:
            if self.consume(tokens):
                return
            time.sleep(max(0.01, 1.0 / self.rate))
