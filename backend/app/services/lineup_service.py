"""Service compositions (lineups) — Phase 4D."""
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lineup import Lineup, LineupPlayer
from app.models.match import Match
from app.models.team import Team
from app.services.api_football_client import api_football_client

logger = logging.getLogger(__name__)

# Mapping formation -> score offensif/defensif
# Plus la formation est offensive, plus le score offensif est eleve
FORMATION_PROFILE = {
    "4-3-3":  {"attack": 0.8, "defense": 0.6},
    "4-2-3-1":{"attack": 0.7, "defense": 0.7},
    "4-4-2":  {"attack": 0.7, "defense": 0.7},
    "3-5-2":  {"attack": 0.7, "defense": 0.5},
    "3-4-3":  {"attack": 0.9, "defense": 0.4},
    "5-3-2":  {"attack": 0.5, "defense": 0.9},
    "5-4-1":  {"attack": 0.3, "defense": 1.0},
    "4-5-1":  {"attack": 0.4, "defense": 0.8},
    "4-1-4-1":{"attack": 0.6, "defense": 0.7},
    "4-3-2-1":{"attack": 0.6, "defense": 0.7},
}
DEFAULT_PROFILE = {"attack": 0.6, "defense": 0.6}


def import_lineups_for_match(match_id: int, db: Session) -> int:
    """Importe les compositions depuis api-football pour un match.

    Returns:
        Nombre de compositions inserees (0, 1 ou 2).
    """
    match = db.get(Match, match_id)
    if not match or not match.api_football_id:
        logger.warning("Match %d sans api_football_id, skip.", match_id)
        return 0

    try:
        data = api_football_client._get(
            "/fixtures/lineups",
            params={"fixture": match.api_football_id},
        )
        lineups_data = data.get("response", [])
    except Exception as exc:
        logger.error("Erreur API lineups match %d : %s", match_id, exc)
        return 0

    if not lineups_data:
        logger.info("Compositions non disponibles pour match %d", match_id)
        return 0

    count = 0
    for lineup_data in lineups_data:
        team_api_id = lineup_data.get("team", {}).get("id")
        db_team = db.execute(
            select(Team).where(Team.api_football_id == team_api_id)
        ).scalar_one_or_none()

        if not db_team:
            logger.warning("Equipe api_id=%s introuvable, skip.", team_api_id)
            continue

        # Verifier si lineup existe deja
        existing = db.execute(
            select(Lineup).where(
                Lineup.match_id == match_id,
                Lineup.team_id  == db_team.id,
            )
        ).scalar_one_or_none()

        formation  = lineup_data.get("formation")
        coach_name = lineup_data.get("coach", {}).get("name")

        if existing:
            existing.formation  = formation
            existing.coach_name = coach_name
            lineup = existing
        else:
            lineup = Lineup(
                match_id   = match_id,
                team_id    = db_team.id,
                formation  = formation,
                coach_name = coach_name,
            )
            db.add(lineup)
            db.flush()
            count += 1

        # Supprimer anciens joueurs si mise a jour
        if existing:
            db.execute(
                LineupPlayer.__table__.delete().where(
                    LineupPlayer.lineup_id == lineup.id
                )
            )

        # Inserer les joueurs
        for player_data in lineup_data.get("startXI", []):
            p = player_data.get("player", {})
            db.add(LineupPlayer(
                lineup_id              = lineup.id,
                api_football_player_id = p.get("id"),
                player_name            = p.get("name"),
                number                 = p.get("number"),
                position               = p.get("pos"),
                grid                   = p.get("grid"),
                is_starter             = True,
            ))

        for player_data in lineup_data.get("substitutes", []):
            p = player_data.get("player", {})
            db.add(LineupPlayer(
                lineup_id              = lineup.id,
                api_football_player_id = p.get("id"),
                player_name            = p.get("name"),
                number                 = p.get("number"),
                position               = p.get("pos"),
                grid                   = p.get("grid"),
                is_starter             = False,
            ))

    db.commit()
    logger.info("Match %d : %d compositions importees", match_id, count)
    return count


def get_lineups_for_match(match_id: int, db: Session) -> list[Lineup]:
    """Retourne les compositions avec joueurs pour un match."""
    from sqlalchemy.orm import selectinload
    return db.execute(
        select(Lineup)
        .options(selectinload(Lineup.players))
        .where(Lineup.match_id == match_id)
    ).scalars().all()


def compute_formation_factor(
    home_team_id: int,
    away_team_id: int,
    match_id: int,
    db: Session,
) -> tuple[float, float]:
    """Calcule un facteur tactique base sur les formations.

    Principe :
      - Formation offensive vs formation defensive -> avantage offensif
      - Retourne des multiplicateurs appliques sur les lambdas Poisson

    Returns:
        (factor_home, factor_away) : multiplicateurs entre 0.9 et 1.1
    """
    lineups = db.execute(
        select(Lineup).where(Lineup.match_id == match_id)
    ).scalars().all()

    if not lineups:
        return 1.0, 1.0

    home_lineup = next((l for l in lineups if l.team_id == home_team_id), None)
    away_lineup = next((l for l in lineups if l.team_id == away_team_id), None)

    home_profile = FORMATION_PROFILE.get(home_lineup.formation, DEFAULT_PROFILE) if home_lineup else DEFAULT_PROFILE
    away_profile = FORMATION_PROFILE.get(away_lineup.formation, DEFAULT_PROFILE) if away_lineup else DEFAULT_PROFILE

    # Facteur home : attaque home vs defense away
    fh = 1.0 + 0.1 * (home_profile["attack"] - away_profile["defense"])
    # Facteur away : attaque away vs defense home
    fa = 1.0 + 0.1 * (away_profile["attack"] - home_profile["defense"])

    # Borner entre 0.9 et 1.1
    fh = max(0.9, min(1.1, fh))
    fa = max(0.9, min(1.1, fa))

    if home_lineup and away_lineup:
        logger.info(
            "Formations : %s vs %s -> fh=%.3f fa=%.3f",
            home_lineup.formation, away_lineup.formation, fh, fa,
        )
    return fh, fa
