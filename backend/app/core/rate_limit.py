import time
from dataclasses import dataclass, field

from app.core.errors import AppError


@dataclass
class FixedWindowRateLimiter:
    limit: int
    window_seconds: int
    _hits: dict[str, list[float]] = field(default_factory=dict)

    def check(self, key: str) -> int | None:
        if self.limit <= 0:
            return None
        now = time.monotonic()
        cutoff = now - self.window_seconds
        hits = [hit for hit in self._hits.get(key, []) if hit > cutoff]
        if len(hits) >= self.limit:
            oldest = min(hits)
            retry_after = max(1, int(self.window_seconds - (now - oldest)))
            self._hits[key] = hits
            return retry_after
        hits.append(now)
        self._hits[key] = hits
        return None


def raise_rate_limited(retry_after: int) -> None:
    raise AppError(
        code="RATE_LIMITED",
        message="Too many summary generation requests. Please wait before retrying.",
        status_code=429,
        details=[{"retry_after_seconds": retry_after}],
    )
