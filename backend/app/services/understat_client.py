"""Client Understat pour recuperer le xG de la saison courante (Phase 3C).

Understat fournit le xG gratuitement pour les 5 grands championnats europeens,
saison courante incluse. C'est notre source principale pour combler la limite
du plan gratuit api-football (bloque apres 2024).

Strategie :
- On telecharge tous les matchs d'une ligue/saison en une seule requete
- On met en cache 6h (les xG ne changent pas apres le match)
- On fait la correspondance avec notre BDD par nom d'equipe + date (+/-1 jour)
"""

import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_CACHE_TTL = 21600  # 6 heures

# Mapping code competition football-data.org -> nom ligue Understat
COMPETITION_TO_UNDERSTAT: dict[str, str] = {
    "FL1": "Ligue_1",
    "PL":  "EPL",
    "PD":  "La_Liga",
    "BL1": "Bundesliga",
    "SA":  "Serie_A",
}

# Mapping nom Understat -> noms possibles dans notre BDD
# Understat utilise des noms courts, notre BDD des noms complets
UNDERSTAT_TO_DB_NAMES: dict[str, list[str]] = {
    "Paris Saint Germain": ["Paris Saint-Germain FC", "Paris Saint-Germain"],
    "Manchester United":   ["Manchester United FC", "Manchester United"],
    "Manchester City":     ["Manchester City FC", "Manchester City"],
    "Tottenham":           ["Tottenham Hotspur FC", "Tottenham Hotspur"],
    "Newcastle United":    ["Newcastle United FC", "Newcastle United"],
    "Nottingham Forest":   ["Nottingham Forest FC", "Nottingham Forest"],
    "West Ham":            ["West Ham United FC", "West Ham United"],
    "Wolverhampton Wanderers": ["Wolverhampton Wanderers FC", "Wolverhampton Wanderers"],
    "Leicester":           ["Leicester City FC", "Leicester City"],
    "Brighton":            ["Brighton & Hove Albion FC", "Brighton & Hove Albion"],
    "Ipswich":             ["Ipswich Town FC", "Ipswich Town"],
    "Atletico Madrid":     ["Club Atletico de Madrid", "Atletico de Madrid"],
    "Milan":               ["AC Milan"],
    "Inter":               ["Inter Milan", "FC Internazionale Milano"],
    "Napoli":              ["SSC Napoli"],
    "Lazio":               ["SS Lazio"],
    "Roma":                ["AS Roma"],
    "Juventus":            ["Juventus FC"],
    "Fiorentina":          ["ACF Fiorentina"],
    "Atalanta":            ["Atalanta BC"],
    "Verona":              ["Hellas Verona FC"],
    "Lecce":               ["US Lecce"],
    "Como":                ["Como 1907"],
    "Bologna":             ["Bologna FC 1909"],
    "Bayern Munich":       ["FC Bayern Munchen", "FC Bayern Munich"],
    "Dortmund":            ["Borussia Dortmund"],
    "Leverkusen":          ["Bayer 04 Leverkusen"],
    "RB Leipzig":          ["RB Leipzig"],
    "Frankfurt":           ["Eintracht Frankfurt"],
    "Monchengladbach":     ["Borussia Monchengladbach"],
    "Freiburg":            ["Sport-Club Freiburg"],
    "Hoffenheim":          ["TSG 1899 Hoffenheim"],
    "Wolfsburg":           ["VfL Wolfsburg"],
    "Marseille":           ["Olympique de Marseille"],
    "Lyon":                ["Olympique Lyonnais"],
    "Monaco":              ["AS Monaco FC"],
    "Lens":                ["RC Lens"],
    "Rennes":              ["Stade Rennais FC"],
    "Le Havre":            ["Le Havre AC"],
    "Real Madrid":         ["Real Madrid CF"],
    "Barcelona":           ["FC Barcelona"],
    "Sevilla":             ["Sevilla FC"],
    "Villarreal":          ["Villarreal CF"],
    "Real Sociedad":       ["Real Sociedad de Futbol"],
    "Athletic Club":       ["Athletic Club"],
}


class UnderstatClient:
    """Client Understat avec cache memoire TTL 6h.

    Attributes:
        _cache: Dict (league, season) -> (data, timestamp)
    """

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], tuple[list[dict], float]] = {}

    def _get_league_data(self, league: str, season: str) -> list[dict]:
        """Recupere tous les matchs d'une ligue/saison avec cache.

        Args:
            league: Nom Understat (ex: "Ligue_1", "EPL").
            season: Annee de debut (ex: "2025" pour 2025-26).

        Returns:
            Liste de matchs avec xG, score, datetime, equipes.
        """
        key = (league, season)
        if key in self._cache:
            data, ts = self._cache[key]
            if time.monotonic() - ts < _CACHE_TTL:
                logger.debug("Cache Understat hit: %s %s", league, season)
                return data

        import understatapi
        client = understatapi.UnderstatClient()
        logger.info("Understat fetch: %s saison %s", league, season)
        matches = client.league(league=league).get_match_data(season=season)
        self._cache[key] = (matches, time.monotonic())
        logger.info("Understat: %d matchs recuperes pour %s %s", len(matches), league, season)
        return matches

    def get_xg_for_match(
        self,
        competition_code: str,
        home_team_db_name: str,
        away_team_db_name: str,
        match_date: datetime,
    ) -> tuple[float, float] | None:
        """Trouve le xG d'un match par correspondance nom+date.

        Args:
            competition_code:  Code football-data.org (ex: "FL1").
            home_team_db_name: Nom de l'equipe domicile dans notre BDD.
            away_team_db_name: Nom de l'equipe exterieure dans notre BDD.
            match_date:        Date du match (timezone-aware).

        Returns:
            (xg_home, xg_away) ou None si non trouve.
        """
        league = COMPETITION_TO_UNDERSTAT.get(competition_code)
        if league is None:
            logger.debug("Ligue %s non couverte par Understat.", competition_code)
            return None

        # Determiner la saison
        season = str(match_date.year if match_date.month >= 7 else match_date.year - 1)

        try:
            matches = self._get_league_data(league, season)
        except Exception as exc:
            logger.error("Erreur Understat %s %s : %s", league, season, exc)
            return None

        # Normaliser le nom BDD -> nom court pour comparaison
        home_short = self._db_name_to_understat(home_team_db_name)
        away_short = self._db_name_to_understat(away_team_db_name)

        if match_date.tzinfo is None:
            match_date = match_date.replace(tzinfo=timezone.utc)

        for m in matches:
            if not m.get("isResult"):
                continue

            m_home = m["h"]["title"]
            m_away = m["a"]["title"]

            # Correspondance noms
            home_match = (m_home == home_short or m_home == home_team_db_name)
            away_match = (m_away == away_short or m_away == away_team_db_name)

            if not (home_match and away_match):
                continue

            # Correspondance date (+/- 1 jour pour absorber fuseaux horaires)
            try:
                m_date = datetime.strptime(m["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if abs((m_date - match_date).days) <= 1:
                    xg_h = float(m["xG"]["h"])
                    xg_a = float(m["xG"]["a"])
                    logger.info(
                        "xG Understat trouve : %s vs %s -> h=%.2f a=%.2f",
                        m_home, m_away, xg_h, xg_a,
                    )
                    return xg_h, xg_a
            except (ValueError, KeyError):
                continue

        logger.debug("xG non trouve sur Understat : %s vs %s", home_team_db_name, away_team_db_name)
        return None

    def get_recent_xg(
        self,
        competition_code: str,
        team_db_name: str,
        match_date: datetime,
        n: int = 5,
    ) -> list[float]:
        """Recupere les xG des n derniers matchs d'une equipe avant match_date.

        Utilise pour calculer le form_weight xG sans passer par match_stats.

        Args:
            competition_code: Code football-data.org.
            team_db_name:     Nom de l'equipe dans notre BDD.
            match_date:       Date de reference (matchs anterieurs uniquement).
            n:                Nombre de matchs a recuperer.

        Returns:
            Liste de xG (de l'equipe consideree), du plus recent au plus ancien.
        """
        league = COMPETITION_TO_UNDERSTAT.get(competition_code)
        if league is None:
            return []

        season = str(match_date.year if match_date.month >= 7 else match_date.year - 1)

        try:
            matches = self._get_league_data(league, season)
        except Exception:
            return []

        team_short = self._db_name_to_understat(team_db_name)
        if match_date.tzinfo is None:
            match_date = match_date.replace(tzinfo=timezone.utc)

        xg_list: list[tuple[datetime, float]] = []

        for m in matches:
            if not m.get("isResult"):
                continue
            try:
                m_date = datetime.strptime(m["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            if m_date >= match_date:
                continue

            m_home = m["h"]["title"]
            m_away = m["a"]["title"]

            if m_home == team_short or m_home == team_db_name:
                xg_list.append((m_date, float(m["xG"]["h"])))
            elif m_away == team_short or m_away == team_db_name:
                xg_list.append((m_date, float(m["xG"]["a"])))

        # Trier du plus recent au plus ancien et prendre les n derniers
        xg_list.sort(key=lambda x: x[0], reverse=True)
        return [xg for _, xg in xg_list[:n]]

    @staticmethod
    def _db_name_to_understat(db_name: str) -> str:
        """Convertit un nom BDD en nom court Understat.

        Parcourt UNDERSTAT_TO_DB_NAMES pour trouver la correspondance inverse.

        Args:
            db_name: Nom de l'equipe dans notre BDD.

        Returns:
            Nom court Understat ou db_name si non trouve.
        """
        for understat_name, db_names in UNDERSTAT_TO_DB_NAMES.items():
            if db_name in db_names:
                return understat_name
        return db_name


# Singleton
understat_client = UnderstatClient()
