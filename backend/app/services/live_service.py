"""Service live scores — Phase 4E.

Principe :
  - Interroge /fixtures?live=all toutes les 2 minutes
  - Met a jour status + score des matchs IN_PLAY en BDD
  - Permet au frontend de poller /live pour afficher les scores en direct
"""
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.competition import Competition
from app.services.api_football_client import api_football_client

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "1H": "IN_PLAY", "HT": "IN_PLAY", "2H": "IN_PLAY",
    "ET": "IN_PLAY", "BT": "IN_PLAY", "P":  "IN_PLAY",
    "FT": "FINISHED", "AET": "FINISHED", "PEN": "FINISHED",
    "NS": "SCHEDULED", "TBD": "SCHEDULED",
    "CANC": "CANCELLED", "PST": "POSTPONED", "ABD": "CANCELLED",
}


def fetch_live_scores(db: Session) -> dict:
    """Recupere les matchs en cours et met a jour la BDD.

    Returns:
        Dict avec nb matchs mis a jour et liste des matchs live.
    """
    try:
        data = api_football_client._get("/fixtures", params={"live": "all"})
        fixtures = data.get("response", [])
    except Exception as exc:
        logger.error("Erreur API live : %s", exc)
        return {"updated": 0, "live_matches": []}

    if not fixtures:
        logger.info("Aucun match en cours")
        return {"updated": 0, "live_matches": []}

    updated = 0
    live_matches = []

    for fix in fixtures:
        api_id = fix["fixture"]["id"]

        match = db.execute(
            select(Match).where(Match.api_football_id == api_id)
        ).scalar_one_or_none()

        if not match:
            continue

        short  = fix["fixture"]["status"]["short"]
        status = STATUS_MAP.get(short, short)
        elapsed = fix["fixture"]["status"].get("elapsed")
        home_score = fix["goals"]["home"]
        away_score = fix["goals"]["away"]

        # Mise a jour BDD
        changed = (
            match.status     != status or
            match.home_score != home_score or
            match.away_score != away_score
        )
        if changed:
            match.status     = status
            match.home_score = home_score
            match.away_score = away_score
            updated += 1

        live_matches.append({
            "match_id":        match.id,
            "api_football_id": api_id,
            "competition_id":  match.competition_id,
            "home_team_id":    match.home_team_id,
            "away_team_id":    match.away_team_id,
            "home_score":      home_score,
            "away_score":      away_score,
            "status":          status,
            "elapsed":         elapsed,
            "match_date":      match.match_date.isoformat() if match.match_date else None,
        })

    if updated:
        db.commit()
        logger.info("Live : %d matchs mis a jour", updated)

    return {"updated": updated, "live_matches": live_matches}


def update_timed_to_inplay(db: Session) -> int:
    """Passe les matchs TIMED dont l'heure est passée en IN_PLAY localement."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    # Matchs TIMED dont l'heure est passée
    from datetime import timedelta
    matches = db.execute(
        select(Match)
        .where(Match.status.in_(["TIMED", "SCHEDULED"]))
        .where(Match.match_date <= now)
    ).scalars().all()
    updated = 0
    for m in matches:
        if m.match_date <= now - timedelta(hours=2, minutes=30):
            m.status = "FINISHED"
        else:
            m.status = "IN_PLAY"
        updated += 1
    if updated:
        db.commit()
        logger.info("TIMED→IN_PLAY : %d matchs mis a jour", updated)
    return updated


def get_live_matches(db: Session) -> list[Match]:
    """Retourne les matchs actuellement IN_PLAY depuis la BDD."""
    from sqlalchemy.orm import joinedload
    return db.execute(
        select(Match)
        .options(
            joinedload(Match.competition),
            joinedload(Match.home_team),
            joinedload(Match.away_team),
        )
        .where(Match.status == "IN_PLAY")
        .order_by(Match.match_date)
    ).unique().scalars().all()


def get_todays_matches(db: Session) -> list[Match]:
    """Retourne tous les matchs du jour (joues + a venir + en cours)."""
    from sqlalchemy.orm import joinedload
    today = datetime.now(timezone.utc).date()
    return db.execute(
        select(Match)
        .options(
            joinedload(Match.competition),
            joinedload(Match.home_team),
            joinedload(Match.away_team),
        )
        .where(Match.match_date >= today)
        .where(Match.match_date < today.replace(day=today.day + 1))
        .order_by(Match.match_date)
    ).unique().scalars().all()
