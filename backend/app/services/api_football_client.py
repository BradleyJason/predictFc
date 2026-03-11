"""Client HTTP pour api-sports.io (api-football) v3.

Gère : authentification, rate limiting, cache mémoire TTL 1h.

Limites tier gratuit :
- 100 requêtes / jour
- Pas de données live (délai ~1h sur certains endpoints)

Stratégie de cache agressive :
- TTL 1h en mémoire → évite les doublons dans la même session
- Les données sont aussi persistées en BDD (match_stats) pour ne
  jamais re-requêter un match déjà enrichi.
"""

import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 3600   # 1 heure — les stats d'un match ne changent pas
_MAX_RETRIES = 3
_RATE_LIMIT_DELAY = 6.5  # api-football : limite souple, 1s suffit


class ApiFootballClient:
    """Client synchrone pour api-sports.io v3.

    Attributes:
        base_url: URL de base de l'API.
        headers:  En-têtes avec clé d'authentification.
    """

    def __init__(self) -> None:
        self.base_url = settings.api_football_base_url.rstrip("/")
        self.headers = {
            "x-apisports-key": settings.api_football_key,
            "x-apisports-host": "v3.football.api-sports.io",
        }
        self._cache: dict[str, tuple[Any, float]] = {}

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _cache_get(self, key: str) -> Any | None:
        if key in self._cache:
            data, ts = self._cache[key]
            if time.monotonic() - ts < _CACHE_TTL:
                logger.debug("Cache hit: %s", key)
                return data
            del self._cache[key]
        return None

    def _cache_set(self, key: str, data: Any) -> None:
        self._cache[key] = (data, time.monotonic())

    # ------------------------------------------------------------------
    # HTTP core
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        """GET avec retry et cache.

        Args:
            path:   Chemin relatif (ex: /fixtures/statistics).
            params: Query parameters.

        Returns:
            Réponse JSON complète (champ 'response' inclus).

        Raises:
            RuntimeError: Après _MAX_RETRIES échecs.
        """
        url = f"{self.base_url}{path}"
        cache_key = f"{url}?{sorted((params or {}).items())}"

        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.info("ApiFootball GET %s (tentative %d)", url, attempt)
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, headers=self.headers, params=params)

                response.raise_for_status()
                data = response.json()

                # Vérification des erreurs API-Football (code 200 mais erreur dans le body)
                errors = data.get("errors", {})
                if errors:
                    logger.error("API-Football erreur : %s", errors)
                    raise RuntimeError(f"API-Football erreur : {errors}")

                time.sleep(_RATE_LIMIT_DELAY)
                self._cache_set(cache_key, data)
                return data

            except httpx.HTTPStatusError as exc:
                logger.error("HTTP %d sur %s", exc.response.status_code, url)
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    time.sleep(2 ** attempt)
            except httpx.RequestError as exc:
                logger.error("Réseau : %s", exc)
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Échec après {_MAX_RETRIES} tentatives sur {url}") from last_exc

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    def get_fixture_stats(self, fixture_id: int) -> list[dict]:
        """Stats d'un match : possession, tirs, corners, cartons, xG.

        Args:
            fixture_id: ID du match côté api-football.

        Returns:
            Liste de 2 dicts (un par équipe) avec leurs stats.
            Exemple de clés : 'Shots on Goal', 'Ball Possession',
            'Expected Goals', 'Corner Kicks', 'Yellow Cards'...

        Exemple de retour :
            [
              {"team": {"id": 85, "name": "Paris Saint Germain"},
               "statistics": [
                 {"type": "Shots on Goal", "value": 5},
                 {"type": "Ball Possession", "value": "60%"},
                 {"type": "Expected Goals", "value": "2.3"},
                 ...
               ]},
              {"team": {...}, "statistics": [...]}
            ]
        """
        data = self._get("/fixtures/statistics", params={"fixture": fixture_id})
        return data.get("response", [])

    def get_fixture_events(self, fixture_id: int) -> list[dict]:
        """Événements d'un match : buts, cartons, remplacements.

        Args:
            fixture_id: ID du match côté api-football.

        Returns:
            Liste d'événements triés chronologiquement.
            Chaque événement : time, team, player, type, detail.
        """
        data = self._get("/fixtures/events", params={"fixture": fixture_id})
        return data.get("response", [])

    def get_injuries(self, league_id: int, season: int) -> list[dict]:
        """Blessés et suspendus pour une compétition/saison.

        Args:
            league_id: ID de la ligue côté api-football.
            season:    Année (ex: 2024).

        Returns:
            Liste de joueurs blessés/suspendus avec équipe et raison.
        """
        data = self._get("/injuries", params={"league": league_id, "season": season})
        return data.get("response", [])

    def get_standings(self, league_id: int, season: int) -> list[dict]:
        """Classement d'une compétition.

        Args:
            league_id: ID de la ligue.
            season:    Année.

        Returns:
            Classement avec points, buts, forme récente par équipe.
        """
        data = self._get("/standings", params={"league": league_id, "season": season})
        standings = data.get("response", [])
        if standings:
            # La réponse est imbriquée : response[0].league.standings[0]
            return standings[0].get("league", {}).get("standings", [[]])[0]
        return []

    def get_team_stats(self, team_id: int, league_id: int, season: int) -> dict:
        """Stats agrégées d'une équipe sur toute la saison.

        Contient : buts marqués/encaissés, possession moyenne,
        tirs, corners, cartons, forme récente (5 matchs).

        Args:
            team_id:   ID de l'équipe côté api-football.
            league_id: ID de la ligue.
            season:    Année.

        Returns:
            Dict avec toutes les stats de la saison.
        """
        data = self._get(
            "/teams/statistics",
            params={"team": team_id, "league": league_id, "season": season},
        )
        return data.get("response", {})

    def get_fixtures_by_team(
        self,
        team_id: int,
        season: int,
        last: int = 5,
    ) -> list[dict]:
        """Derniers matchs d'une équipe avec stats xG.

        Args:
            team_id: ID de l'équipe.
            season:  Année.
            last:    Nombre de matchs à récupérer (défaut : 5).

        Returns:
            Liste de matchs avec score, xG, et infos générales.
        """
        data = self._get(
            "/fixtures",
            params={"team": team_id, "season": season, "last": last, "status": "FT"},
        )
        return data.get("response", [])

    def search_team(self, name: str) -> list[dict]:
        """Cherche une équipe par nom pour obtenir son ID api-football.

        Args:
            name: Nom de l'équipe (ex: 'Paris Saint-Germain').

        Returns:
            Liste de résultats avec id, name, country.
        """
        data = self._get("/teams", params={"search": name})
        return data.get("response", [])

    def get_fixture_by_date_and_teams(
        self,
        home_team_id: int,
        away_team_id: int,
        season: int,
    ) -> list[dict]:
        """Trouve un match via les IDs d'équipes api-football.

        Utile pour faire le lien entre notre BDD et api-football.

        Args:
            home_team_id: ID domicile côté api-football.
            away_team_id: ID extérieur côté api-football.
            season:       Année.

        Returns:
            Liste de matchs correspondants.
        """
        data = self._get(
            "/fixtures",
            params={
                "team": home_team_id,
                "season": season,
                "status": "FT",
            },
        )
        fixtures = data.get("response", [])
        # Filtre côté client pour garder uniquement les matchs entre ces deux équipes
        return [
            f for f in fixtures
            if f["teams"]["away"]["id"] == away_team_id
        ]

    def check_status(self) -> dict:
        """Vérifie le quota restant (requêtes utilisées / disponibles).

        Returns:
            Dict avec requests_used, requests_limit, requests_remaining.
        """
        data = self._get("/status")
        account = data.get("response", {}).get("requests", {})
        remaining = account.get("limit_day", 100) - account.get("current", 0)
        logger.info(
            "API-Football quota : %d/%d req utilisées, %d restantes",
            account.get("current", 0),
            account.get("limit_day", 100),
            remaining,
        )
        return {
            "requests_used":      account.get("current", 0),
            "requests_limit":     account.get("limit_day", 100),
            "requests_remaining": remaining,
        }


# Singleton partagé
api_football_client = ApiFootballClient()
