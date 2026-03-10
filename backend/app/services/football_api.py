"""Client HTTP pour football-data.org API v4.

Gère : authentification, rate limiting, retry sur 429, cache mémoire TTL 5 min.
"""

import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Codes des compétitions supportées par PredictFC
COMPETITIONS: dict[str, str] = {
    "ligue1": "FL1",
    "premier_league": "PL",
    "champions_league": "CL",
    "la_liga": "PD",
    "bundesliga": "BL1",
    "serie_a": "SA",
}

_RATE_LIMIT_DELAY = 6.0  # 10 req/min → 6s entre chaque requête
_CACHE_TTL = 300  # 5 minutes
_MAX_RETRIES = 3


class FootballAPIClient:
    """Client synchrone pour football-data.org API v4.

    Attributes:
        base_url: URL de base de l'API.
        headers: En-têtes HTTP avec token d'authentification.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialise le client avec la clé API.

        Args:
            api_key: Clé API football-data.org. Si None, utilise les settings.
        """
        self.base_url = settings.football_data_base_url.rstrip("/")
        self.headers = {"X-Auth-Token": api_key or settings.football_data_api_key}
        self._cache: dict[str, tuple[Any, float]] = {}  # url → (data, timestamp)

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _cache_get(self, key: str) -> Any | None:
        """Retourne la valeur du cache si non expirée, None sinon."""
        if key in self._cache:
            data, ts = self._cache[key]
            if time.monotonic() - ts < _CACHE_TTL:
                logger.debug("Cache hit: %s", key)
                return data
            del self._cache[key]
        return None

    def _cache_set(self, key: str, data: Any) -> None:
        """Stocke une valeur dans le cache avec timestamp courant."""
        self._cache[key] = (data, time.monotonic())

    # ------------------------------------------------------------------
    # HTTP core
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        """Effectue une requête GET avec retry sur 429 et rate limiting.

        Args:
            path: Chemin relatif de l'endpoint (ex: /competitions/FL1/matches).
            params: Query parameters optionnels.

        Returns:
            Réponse JSON parsée.

        Raises:
            httpx.HTTPStatusError: Si l'API retourne une erreur non récupérable.
        """
        url = f"{self.base_url}{path}"
        cache_key = f"{url}?{params}"

        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.info("GET %s (tentative %d/%d)", url, attempt, _MAX_RETRIES)
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, headers=self.headers, params=params)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning("Rate limit 429 — attente %ds", retry_after)
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                # Respect du rate limit : 6s entre les requêtes réussies
                time.sleep(_RATE_LIMIT_DELAY)

                self._cache_set(cache_key, data)
                return data

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Erreur HTTP %d sur %s : %s",
                    exc.response.status_code,
                    url,
                    exc.response.text[:200],
                )
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    time.sleep(2**attempt)  # backoff exponentiel
            except httpx.RequestError as exc:
                logger.error("Erreur réseau sur %s : %s", url, exc)
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    time.sleep(2**attempt)

        raise RuntimeError(
            f"Échec après {_MAX_RETRIES} tentatives sur {url}"
        ) from last_exc

    # ------------------------------------------------------------------
    # API endpoints
    # ------------------------------------------------------------------

    def get_competition(self, code: str) -> dict:
        """Récupère les infos d'une compétition.

        Args:
            code: Code de la compétition (ex: FL1, PL, CL).

        Returns:
            Dict avec id, name, code, area, currentSeason, etc.
        """
        return self._get(f"/competitions/{code}")

    def get_matches(
        self,
        code: str,
        season: int,
        statuses: list[str] | None = None,
    ) -> list[dict]:
        """Récupère les matchs d'une compétition pour une saison donnée.

        Args:
            code: Code de la compétition.
            season: Année de début de la saison (ex: 2024 pour 2024-25).
            statuses: Filtres de statut. Défaut: FINISHED, IN_PLAY, SCHEDULED.

        Returns:
            Liste de dicts match (id, utcDate, status, homeTeam, awayTeam, score...).
        """
        if statuses is None:
            statuses = ["FINISHED", "IN_PLAY", "SCHEDULED"]

        params: dict[str, Any] = {
            "season": season,
            "status": ",".join(statuses),
        }
        data = self._get(f"/competitions/{code}/matches", params=params)
        matches: list[dict] = data.get("matches", [])
        logger.info(
            "Compétition %s saison %d : %d matchs récupérés",
            code,
            season,
            len(matches),
        )
        return matches

    def get_teams(self, code: str, season: int) -> list[dict]:
        """Récupère les équipes d'une compétition pour une saison donnée.

        Args:
            code: Code de la compétition.
            season: Année de début de la saison (ex: 2024 pour 2024-25).

        Returns:
            Liste de dicts équipe (id, name, shortName, ...).
        """
        params: dict[str, Any] = {"season": season}
        data = self._get(f"/competitions/{code}/teams", params=params)
        teams: list[dict] = data.get("teams", [])
        logger.info(
            "Compétition %s saison %d : %d équipes récupérées",
            code,
            season,
            len(teams),
        )
        return teams
