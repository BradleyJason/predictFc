"""HTTP client for football-data.org API v4.

Features:
- In-memory cache with 5-minute TTL
- Automatic rate-limit compliance (10 req/min on free plan → sleep 6 s)
- Retry on HTTP 429 with Retry-After header support
- Up to 3 attempts per request
"""
import logging
import time
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

COMPETITIONS = {
    "ligue1":          "FL1",
    "premier_league":  "PL",
    "champions_league": "CL",
    "la_liga":         "PD",
    "bundesliga":      "BL1",
    "serie_a":         "SA",
}


class FootballAPIClient:
    """Synchronous client for football-data.org with TTL cache and retry logic."""

    RATE_LIMIT_SLEEP = 6  # seconds between requests (free plan: 10 req/min)

    def __init__(self) -> None:
        self._base_url = settings.football_data_base_url.rstrip("/")
        self._headers = {"X-Auth-Token": settings.football_data_api_key}
        self._cache: dict[str, tuple[Any, float]] = {}  # key → (data, expires_at)
        self._ttl = 300  # 5 minutes

    # ── Cache helpers ──────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[Any]:
        """Return cached value if still valid, else None."""
        if key in self._cache:
            data, expires_at = self._cache[key]
            if time.monotonic() < expires_at:
                return data
            del self._cache[key]
        return None

    def _cache_set(self, key: str, data: Any) -> None:
        """Store data in cache with TTL expiry."""
        self._cache[key] = (data, time.monotonic() + self._ttl)

    # ── Core HTTP ──────────────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """Perform a GET request with cache, rate limiting, and 429 retry.

        Args:
            path:   API path relative to base URL (e.g. '/competitions/PL/matches')
            params: Optional query parameters dict.

        Returns:
            Parsed JSON response as dict.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses after max retries.
        """
        import httpx

        cache_key = f"{path}?{sorted((params or {}).items())}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.debug("Cache hit: %s", cache_key)
            return cached

        url = f"{self._base_url}/{path.lstrip('/')}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(url, headers=self._headers, params=params)

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning(
                            "Rate limited (429) on %s — sleeping %ds (attempt %d/%d)",
                            path,
                            retry_after,
                            attempt + 1,
                            max_retries,
                        )
                        time.sleep(retry_after)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                    time.sleep(self.RATE_LIMIT_SLEEP)
                    self._cache_set(cache_key, data)
                    return data

            except Exception as exc:
                logger.error(
                    "FootballAPIClient error (attempt %d/%d) for %s: %s",
                    attempt + 1,
                    max_retries,
                    url,
                    exc,
                )
                if attempt == max_retries - 1:
                    raise

        return {}

    # ── Public API methods ─────────────────────────────────────────────────────

    def get_competition(self, code: str) -> dict:
        """GET /competitions/{code} — competition metadata."""
        return self._get(f"/competitions/{code}")

    def get_matches(
        self,
        code: str,
        season: Optional[int] = None,
        statuses: Optional[list[str]] = None,
    ) -> dict:
        """GET /competitions/{code}/matches — matches for a competition/season."""
        params: dict = {}
        if season:
            params["season"] = season
        if statuses:
            params["status"] = ",".join(statuses)
        return self._get(f"/competitions/{code}/matches", params=params)

    def get_teams(self, code: str, season: Optional[int] = None) -> dict:
        """GET /competitions/{code}/teams — teams in a competition."""
        params: dict = {}
        if season:
            params["season"] = season
        return self._get(f"/competitions/{code}/teams", params=params)


# Module-level singleton
football_api_client = FootballAPIClient()
