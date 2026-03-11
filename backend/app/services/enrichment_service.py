"""Service d'enrichissement des matchs via api-football (Phase 3B)."""

import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_stat import MatchStat
from app.models.team import Team
from app.services.api_football_client import api_football_client

logger = logging.getLogger(__name__)

_MAX_AGE_DAYS = 30
_team_id_cache: dict[str, int | None] = {}

# Mots a supprimer pour simplifier la recherche
# "Club Atletico de Madrid" -> "Atletico Madrid"
_NOISE_WORDS = {
    "football", "club", "fc", "afc", "cf", "sc", "ac", "as", "ss", "us",
    "de", "du", "le", "la", "les", "el", "real", "the",
}

# Corrections manuelles pour les noms problematiques
# Cle = nom normalise (sans accents, minuscules), valeur = terme de recherche
_NAME_OVERRIDES: dict[str, str] = {
    "club atletico de madrid": "Atletico Madrid",
    "atletico de madrid": "Atletico Madrid",
    "tottenham hotspur fc": "Tottenham",
    "tottenham hotspur": "Tottenham",
    "paris saint germain": "PSG",
    "paris saint germain fc": "PSG",
    "manchester united fc": "Manchester United",
    "manchester city fc": "Manchester City",
    "borussia monchengladbach": "Monchengladbach",
    "bayer 04 leverkusen": "Leverkusen",
    "rb leipzig": "RB Leipzig",
    "inter milan": "Inter",
    "internazionale": "Inter",
    "ac milan": "Milan",
}


def _normalize_team_name(name: str) -> str:
    """Normalise un nom d'equipe pour la recherche api-football.

    Etapes :
    1. Verifier les overrides manuels (cas problematiques connus)
    2. Supprimer les accents
    3. Supprimer les caracteres speciaux
    4. Supprimer les mots parasites (FC, Club, de, etc.)

    Args:
        name: Nom brut de l'equipe depuis notre BDD.

    Returns:
        Terme de recherche optimal pour api-football.
    """
    # 1. Override manuel
    key = name.lower().strip()
    if key in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[key]

    # 2. Supprimer les accents
    normalized = unicodedata.normalize("NFD", name)
    without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # 3. Supprimer les caracteres speciaux
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", " ", without_accents)

    # 4. Supprimer les mots parasites
    words = cleaned.split()
    filtered = [w for w in words if w.lower() not in _NOISE_WORDS]
    result = " ".join(filtered) if filtered else cleaned

    return re.sub(r" +", " ", result).strip()


def _find_best_team_match(results: list[dict], search_name: str) -> int | None:
    """Choisit le meilleur resultat parmi les equipes retournees.

    api-football peut retourner plusieurs equipes pour un meme nom
    (ex: equipe masculine et feminine). On prefere :
    1. L'equipe masculine (pas de "W", "Women", "Ladies" dans le nom)
    2. Le resultat avec le plus grand nombre de matchs joues

    Args:
        results:     Liste de resultats api-football.
        search_name: Terme de recherche utilise (pour les logs).

    Returns:
        ID api-football de la meilleure equipe, ou None.
    """
    if not results:
        return None

    # Filtrer les equipes feminines
    FEMININE_KEYWORDS = {"w", "women", "ladies", "feminin", "feminine"}
    masculine = [
        r for r in results
        if not any(
            kw in r["team"]["name"].lower().split()
            for kw in FEMININE_KEYWORDS
        )
    ]

    candidates = masculine if masculine else results
    # Prendre le premier candidat (api-football trie par pertinence)
    return candidates[0]["team"]["id"]


def _parse_stat(value, as_float=False):
    """Parse une valeur de stat api-football (str, int, float ou None)."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace("%", "").strip()
        if not value:
            return None
        try:
            return float(value) if as_float else int(float(value))
        except ValueError:
            return None
    return float(value) if as_float else int(value)


def _get_api_football_team_id(team_name: str) -> int | None:
    """Trouve l'ID api-football d'une equipe avec normalisation intelligente."""
    if team_name in _team_id_cache:
        return _team_id_cache[team_name]

    clean_name = _normalize_team_name(team_name)
    logger.debug("Recherche equipe : %r -> %r", team_name, clean_name)

    results = api_football_client.search_team(clean_name)
    team_id = _find_best_team_match(results, clean_name)

    if team_id is None:
        logger.warning("Equipe non trouvee : %s (recherche: %s)", team_name, clean_name)
        _team_id_cache[team_name] = None
        return None

    logger.debug("Equipe %r -> ID %d", team_name, team_id)
    _team_id_cache[team_name] = team_id
    return team_id


def _find_fixture_id(home_name: str, away_name: str, match_date: datetime) -> int | None:
    """Trouve l'ID fixture api-football pour un match de notre BDD."""
    home_api_id = _get_api_football_team_id(home_name)
    away_api_id = _get_api_football_team_id(away_name)

    if home_api_id is None or away_api_id is None:
        return None

    season = match_date.year if match_date.month >= 7 else match_date.year - 1
    fixtures = api_football_client.get_fixture_by_date_and_teams(home_api_id, away_api_id, season)

    if not fixtures:
        logger.warning("Fixture non trouve : %s vs %s", home_name, away_name)
        return None

    if match_date.tzinfo is None:
        match_date = match_date.replace(tzinfo=timezone.utc)

    for fixture in fixtures:
        fixture_date_str = fixture.get("fixture", {}).get("date", "")
        try:
            fixture_date = datetime.fromisoformat(fixture_date_str)
            if fixture_date.tzinfo is None:
                fixture_date = fixture_date.replace(tzinfo=timezone.utc)
            if abs((fixture_date - match_date).days) <= 3:
                fixture_id = fixture["fixture"]["id"]
                logger.info("Fixture trouve : %s vs %s -> %d", home_name, away_name, fixture_id)
                return fixture_id
        except (ValueError, KeyError):
            continue

    logger.warning("Aucun fixture dans la fenetre de dates pour %s vs %s", home_name, away_name)
    return None


def _stats_list_to_dict(statistics: list) -> dict:
    return {s["type"]: s["value"] for s in statistics}


def enrich_match(match_id: int, db: Session) -> bool:
    """Enrichit un match avec les stats api-football."""
    match = db.get(Match, match_id)
    if not match:
        return False
    if match.status != "FINISHED":
        return False

    now = datetime.now(timezone.utc)
    match_date = match.match_date
    if match_date.tzinfo is None:
        match_date = match_date.replace(tzinfo=timezone.utc)

    if (now - match_date).days > _MAX_AGE_DAYS:
        logger.debug("Match %d trop ancien, skip.", match_id)
        return False

    existing = db.scalars(select(MatchStat).where(MatchStat.match_id == match_id)).first()
    if existing:
        return True

    home_team = db.get(Team, match.home_team_id)
    away_team = db.get(Team, match.away_team_id)
    if not home_team or not away_team:
        return False

    fixture_id = _find_fixture_id(home_team.name, away_team.name, match_date)
    if fixture_id is None:
        return False

    try:
        stats_response = api_football_client.get_fixture_stats(fixture_id)
    except Exception as exc:
        logger.error("Erreur api-football fixture %d : %s", fixture_id, exc)
        return False

    if len(stats_response) < 2:
        return False

    sides = [
        (stats_response[0], match.home_team_id, "HOME"),
        (stats_response[1], match.away_team_id, "AWAY"),
    ]

    for team_data, team_id, side in sides:
        raw = _stats_list_to_dict(team_data.get("statistics", []))
        stat = MatchStat(
            match_id=match_id,
            team_id=team_id,
            side=side,
            api_football_fixture_id=fixture_id,
            shots_total=_parse_stat(raw.get("Total Shots")),
            shots_on_goal=_parse_stat(raw.get("Shots on Goal")),
            shots_off_goal=_parse_stat(raw.get("Shots off Goal")),
            shots_blocked=_parse_stat(raw.get("Blocked Shots")),
            ball_possession=_parse_stat(raw.get("Ball Possession"), as_float=True),
            passes_total=_parse_stat(raw.get("Total passes")),
            passes_accurate=_parse_stat(raw.get("Passes accurate")),
            passes_pct=_parse_stat(raw.get("Passes %"), as_float=True),
            corner_kicks=_parse_stat(raw.get("Corner Kicks")),
            fouls=_parse_stat(raw.get("Fouls")),
            offsides=_parse_stat(raw.get("Offsides")),
            yellow_cards=_parse_stat(raw.get("Yellow Cards")),
            red_cards=_parse_stat(raw.get("Red Cards")),
            goalkeeper_saves=_parse_stat(raw.get("Goalkeeper Saves")),
            expected_goals=_parse_stat(
                raw.get("expected_goals") or raw.get("Expected Goals"), as_float=True
            ),
        )
        db.add(stat)

    db.commit()
    logger.info("Match %d enrichi (fixture_id=%d).", match_id, fixture_id)
    return True


def enrich_recent_matches(db: Session, limit: int = 10) -> dict:
    """Enrichit les matchs FINISHED recents non encore enrichis."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_MAX_AGE_DAYS)

    candidates = db.scalars(
        select(Match)
        .where(
            Match.status == "FINISHED",
            Match.match_date >= cutoff,
            ~Match.id.in_(select(MatchStat.match_id).distinct()),
        )
        .order_by(Match.match_date.desc())
        .limit(limit)
    ).all()

    results = {"enriched": 0, "skipped": 0, "failed": 0}
    for match in candidates:
        try:
            success = enrich_match(match.id, db)
            if success:
                results["enriched"] += 1
            else:
                results["skipped"] += 1
        except Exception as exc:
            logger.error("Erreur enrichissement match %d : %s", match.id, exc)
            results["failed"] += 1

    logger.info("Enrichissement termine : %s", results)
    return results
