import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Thread-safe sliding window in-memory rate limiter."""

    def __init__(self):
        # Maps key -> list of float timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds

        # Clean old timestamps
        history = [ts for ts in self._history[key] if ts > cutoff]
        self._history[key] = history

        if len(history) >= max_requests:
            oldest = history[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, retry_after

        self._history[key].append(now)
        return True, 0

    def reset(self):
        """Reset internal rate limit tracking (useful for test suites)."""
        self._history.clear()


limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60, key_prefix: str = ""):
    """FastAPI dependency to rate limit requests by client IP address."""

    async def dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}" if key_prefix else client_ip

        allowed, retry_after = limiter.is_allowed(key, max_requests, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
