"""Service import et consultation des blessures/suspensions (Phase 4B)."""
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.injury import Injury
from app.models.match import Match
from app.models.season import Season
from app.models.team import Team
from app.services.api_football_client import api_football_client

logger = logging.getLogger(__name__)


def import_injuries_for_match(match_id: int, db: Session) -> int:
    """Importe les blessures/suspensions pour un match specifique.

    Logique :
      1. Recuperer le match + competition + saison
      2. Appeler /injuries?fixture={api_football_id}
      3. Upsert en BDD (eviter les doublons)

    Returns:
        Nombre de blessures inserees/mises a jour.
    """
    match = db.get(Match, match_id)
    if not match or not match.api_football_id:
        logger.warning("Match %d sans api_football_id, skip.", match_id)
        return 0

    comp = db.get(Competition, match.competition_id) if match.competition_id else None
    if not comp or not comp.api_football_id:
        logger.warning("Competition introuvable pour match %d, skip.", match_id)
        return 0

    season = db.get(Season, match.season_id) if match.season_id else None
    season_year = season.year if season else datetime.now(timezone.utc).year

    try:
        data = api_football_client._get(
            "/injuries",
            params={
                "fixture": match.api_football_id,
            },
        )
        injuries_data = data.get("response", [])
    except Exception as exc:
        logger.error("Erreur API injuries match %d : %s", match_id, exc)
        return 0

    if not injuries_data:
        logger.info("Aucune blessure pour match %d", match_id)
        return 0

    count = 0
    for entry in injuries_data:
        player = entry.get("player", {})
        team   = entry.get("team", {})

        # Retrouver l equipe en BDD via api_football_id
        db_team = db.execute(
            select(Team).where(Team.api_football_id == team.get("id"))
        ).scalar_one_or_none()

        if not db_team:
            logger.debug("Equipe api_id=%s introuvable, skip.", team.get("id"))
            continue

        # Verifier doublon (meme fixture + meme joueur)
        existing = db.execute(
            select(Injury).where(
                Injury.fixture_id == match.api_football_id,
                Injury.player_api_id == player.get("id"),
            )
        ).scalar_one_or_none()

        if existing:
            # Mise a jour
            existing.injury_type = entry.get("type")
            existing.reason      = player.get("reason")
        else:
            injury = Injury(
                team_id      = db_team.id,
                match_id     = match_id,
                season_id    = match.season_id,
                fixture_id   = match.api_football_id,
                player_name  = player.get("name"),
                player_api_id= player.get("id"),
                injury_type  = entry.get("type"),
                reason       = player.get("reason"),
            )
            db.add(injury)
            count += 1

    db.commit()
    logger.info("Match %d : %d blessures importees", match_id, count)
    return count


def get_injuries_for_match(match_id: int, db: Session) -> list[Injury]:
    """Retourne les blessures connues pour un match."""
    return db.execute(
        select(Injury)
        .where(Injury.match_id == match_id)
        .order_by(Injury.team_id)
    ).scalars().all()


def compute_injury_penalty(
    home_team_id: int,
    away_team_id: int,
    match_id: int,
    db: Session,
) -> tuple[float, float]:
    """Calcule un coefficient de penalite base sur les blessures.

    Principe :
      - Chaque joueur "Missing Fixture" = -3% sur la force de l equipe
      - Chaque joueur "Doubtful"        = -1% sur la force de l equipe
      - Max penalite : -15% (evite de trop penaliser)

    Returns:
        (penalty_home, penalty_away) : multiplicateurs entre 0.85 et 1.0
    """
    injuries = db.execute(
        select(Injury).where(Injury.match_id == match_id)
    ).scalars().all()

    def _penalty(team_id: int) -> float:
        team_injuries = [i for i in injuries if i.team_id == team_id]
        penalty = 0.0
        for inj in team_injuries:
            if inj.injury_type == "Missing Fixture":
                penalty += 0.03
            elif inj.injury_type == "Doubtful":
                penalty += 0.01
        return max(0.85, 1.0 - penalty)  # Plancher a 0.85

    ph = _penalty(home_team_id)
    pa = _penalty(away_team_id)

    if ph < 1.0 or pa < 1.0:
        logger.info(
            "Penalites blessures : home=%.3f away=%.3f (%d blessures)",
            ph, pa, len(injuries),
        )
    return ph, pa
