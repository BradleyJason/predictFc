"""Pipeline d'ingestion des données football-data.org → Supabase (PostgreSQL).

Usage:
    python ml/pipelines/ingest.py
    python ml/pipelines/ingest.py --seasons 2024 2023 --leagues FL1 PL

Stratégie :
- Upsert (INSERT … ON CONFLICT DO UPDATE) → jamais de doublons
- Rate limiting respecté : 6s entre chaque requête API
- Logs structurés à chaque étape
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Ajoute backend/ au path pour importer FootballAPIClient et settings
_BACKEND_PATH = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(_BACKEND_PATH))

from app.core.config import settings  # noqa: E402
from app.services.football_api import COMPETITIONS, FootballAPIClient  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("predictfc.ingest")

# ---------------------------------------------------------------------------
# Définition des tables SQLAlchemy Core (pour l'upsert sans ORM)
# ---------------------------------------------------------------------------

_metadata = MetaData()

competitions_t = Table(
    "competitions",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String(10), unique=True, nullable=False),
    Column("name", String(100), nullable=False),
    Column("country", String(50)),
    Column("season", String(10)),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

teams_t = Table(
    "teams",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("external_id", Integer, unique=True),
    Column("name", String(100), nullable=False),
    Column("short_name", String(50)),
    Column("competition_id", Integer),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

matches_t = Table(
    "matches",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("external_id", Integer, unique=True),
    Column("competition_id", Integer),
    Column("home_team_id", Integer),
    Column("away_team_id", Integer),
    Column("match_date", DateTime(timezone=True), nullable=False),
    Column("status", String(20)),
    Column("home_score", Integer),
    Column("away_score", Integer),
    Column("matchday", Integer),
    Column("stage", String(50)),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), server_default=func.now()),
)

# ---------------------------------------------------------------------------
# Helpers upsert
# ---------------------------------------------------------------------------


def _upsert_competition(conn, comp_info: dict, season: str) -> int:
    """Upsert une compétition, retourne son ID interne.

    Args:
        conn: Connexion SQLAlchemy active.
        comp_info: Dict retourné par get_competition() de l'API.
        season: Ex. "2024-25".

    Returns:
        ID interne (colonne id) de la compétition.
    """
    row = {
        "code": comp_info["code"],
        "name": comp_info["name"],
        "country": comp_info.get("area", {}).get("name"),
        "season": season,
    }
    stmt = (
        pg_insert(competitions_t)
        .values(**row)
        .on_conflict_do_update(
            index_elements=["code"],
            set_={"name": row["name"], "season": row["season"]},
        )
        .returning(competitions_t.c.id)
    )
    result = conn.execute(stmt)
    comp_id: int = result.scalar_one()
    logger.info("Competition upsertée : %s (id=%d)", row["code"], comp_id)
    return comp_id


def _upsert_teams(conn, teams: list[dict], competition_id: int) -> dict[int, int]:
    """Upsert une liste d'équipes, retourne le mapping external_id → internal_id.

    Args:
        conn: Connexion SQLAlchemy active.
        teams: Liste de dicts équipe depuis l'API.
        competition_id: ID interne de la compétition.

    Returns:
        Dict {external_id: internal_id}.
    """
    mapping: dict[int, int] = {}
    for team in teams:
        ext_id: int = team["id"]
        row = {
            "external_id": ext_id,
            "name": team["name"],
            "short_name": team.get("shortName") or team.get("tla"),
            "competition_id": competition_id,
        }
        stmt = (
            pg_insert(teams_t)
            .values(**row)
            .on_conflict_do_update(
                index_elements=["external_id"],
                set_={
                    "name": row["name"],
                    "short_name": row["short_name"],
                    "competition_id": competition_id,
                },
            )
            .returning(teams_t.c.id)
        )
        internal_id: int = conn.execute(stmt).scalar_one()
        mapping[ext_id] = internal_id

    logger.info("%d équipes upsertées pour competition_id=%d", len(mapping), competition_id)
    return mapping


def _upsert_matches(
    conn,
    matches: list[dict],
    competition_id: int,
    team_mapping: dict[int, int],
) -> int:
    """Upsert une liste de matchs.

    Args:
        conn: Connexion SQLAlchemy active.
        matches: Liste de dicts match depuis l'API.
        competition_id: ID interne de la compétition.
        team_mapping: Dict {external_id: internal_id} des équipes.

    Returns:
        Nombre de matchs upsertés.
    """
    count = 0
    for match in matches:
        home_ext = match.get("homeTeam", {}).get("id")
        away_ext = match.get("awayTeam", {}).get("id")
        home_id = team_mapping.get(home_ext) if home_ext else None
        away_id = team_mapping.get(away_ext) if away_ext else None

        score = match.get("score", {}).get("fullTime", {})
        home_score = score.get("home")
        away_score = score.get("away")

        # parse utcDate → datetime
        match_date_str: str = match.get("utcDate", "")
        try:
            match_date = datetime.fromisoformat(match_date_str.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("Date invalide pour match %d : %s", match["id"], match_date_str)
            continue

        row = {
            "external_id": match["id"],
            "competition_id": competition_id,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "match_date": match_date,
            "status": match.get("status"),
            "home_score": home_score,
            "away_score": away_score,
            "matchday": match.get("matchday"),
            "stage": match.get("stage"),
            "updated_at": datetime.utcnow(),
        }
        stmt = (
            pg_insert(matches_t)
            .values(**row)
            .on_conflict_do_update(
                index_elements=["external_id"],
                set_={
                    "status": row["status"],
                    "home_score": row["home_score"],
                    "away_score": row["away_score"],
                    "matchday": row["matchday"],
                    "stage": row["stage"],
                    "updated_at": row["updated_at"],
                },
            )
        )
        conn.execute(stmt)
        count += 1

    logger.info("%d matchs upsertés pour competition_id=%d", count, competition_id)
    return count


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------


def _season_label(year: int) -> str:
    """Retourne le label de saison 'YYYY-YY' depuis l'année de début.

    Args:
        year: Année de début de la saison (ex: 2024).

    Returns:
        Ex: "2024-25".
    """
    return f"{year}-{str(year + 1)[-2:]}"


def run(
    leagues: list[str] | None = None,
    seasons: list[int] | None = None,
) -> None:
    """Lance le pipeline d'ingestion complet.

    Args:
        leagues: Liste de codes compétition à ingérer. Défaut: toutes.
        seasons: Années de début de saison à ingérer. Défaut: [2024, 2023].
    """
    if leagues is None:
        leagues = list(COMPETITIONS.values())
    if seasons is None:
        seasons = [2024, 2023]

    logger.info(
        "Démarrage ingestion — ligues: %s | saisons: %s",
        leagues,
        [_season_label(s) for s in seasons],
    )

    client = FootballAPIClient()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    total_matches = 0

    with engine.begin() as conn:
        for code in leagues:
            for season_year in seasons:
                season_label = _season_label(season_year)
                logger.info("=== %s — saison %s ===", code, season_label)

                # 1. Compétition
                try:
                    comp_info = client.get_competition(code)
                except Exception as exc:
                    logger.error("Impossible de récupérer la compétition %s : %s", code, exc)
                    continue

                comp_id = _upsert_competition(conn, comp_info, season_label)

                # 2. Équipes
                try:
                    teams = client.get_teams(code, season_year)
                except Exception as exc:
                    logger.error(
                        "Impossible de récupérer les équipes de %s/%s : %s",
                        code, season_label, exc,
                    )
                    teams = []

                team_mapping = _upsert_teams(conn, teams, comp_id) if teams else {}

                # 3. Matchs (tous statuts)
                try:
                    matches = client.get_matches(
                        code,
                        season_year,
                        statuses=["FINISHED", "IN_PLAY", "SCHEDULED"],
                    )
                except Exception as exc:
                    logger.error(
                        "Impossible de récupérer les matchs de %s/%s : %s",
                        code, season_label, exc,
                    )
                    continue

                n = _upsert_matches(conn, matches, comp_id, team_mapping)
                total_matches += n

    logger.info("Ingestion terminée — %d matchs upsertés au total.", total_matches)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestion football-data.org → BDD")
    parser.add_argument(
        "--leagues",
        nargs="+",
        default=None,
        help="Codes compétition (ex: FL1 PL CL). Défaut: toutes.",
    )
    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=None,
        help="Années de début de saison (ex: 2024 2023). Défaut: 2024 2023.",
    )
    args = parser.parse_args()
    run(leagues=args.leagues, seasons=args.seasons)
