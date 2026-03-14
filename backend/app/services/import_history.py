"""Script d'import historique api-football — Phase 4A.

Stratégie :
- Import par batch avec respect du quota (7500 req/jour)
- Reprise automatique en cas d'interruption (checkpoint)
- Priorité : fixtures → stats → events
- Lineups : seulement pour les matchs à venir
"""

import json
import logging
import sys
import time
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, "/mnt/c/STORAGE/PredictFC/predictFc/backend")

from app.core.database import SessionLocal
from app.models.competition import Competition
from app.models.season import Season
from app.models.team import Team
from app.models.match import Match
from app.models.match_stat import MatchStat
from app.models.match_event import MatchEvent
from app.services.api_football_client import api_football_client
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("/tmp/import_history.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Checkpoint pour reprendre en cas d'interruption
CHECKPOINT_FILE = Path("/tmp/import_checkpoint.json")

# Saisons a importer
SEASONS = [2020, 2021, 2022, 2023, 2024, 2025]

# Competitions prioritaires (championnats + CL d'abord)
PRIORITY_COMPETITIONS = [
    ("PL",  39),  ("FL1", 61),  ("PD",  140), ("BL1", 78),
    ("SA",  135), ("CL",  2),   ("EL",  3),   ("ECL", 848),
    ("PPL", 94),  ("DED", 88),  ("BSA", 144), ("TSL", 203),
    ("ENG2",40),
]

# Competitions secondaires (coupes + internationales)
SECONDARY_COMPETITIONS = [
    ("FAC", 45),  ("CDR", 143), ("CIT", 137), ("DFB", 81),
    ("CDL", 66),  ("TAC", 96),  ("KNC", 90),  ("BEL", 146),
    ("TRC", 205), ("EFL", 48),  ("WC",  1),   ("EC",  4),
    ("CA",  9),   ("CAN", 6),   ("AFC", 17),  ("GC",  16),
    ("FCW", 15),  ("CSH", 528), ("SCE", 556), ("SCI", 547),
    ("DFL", 529), ("TCH", 526), ("USC", 531),
]

ALL_COMPETITIONS = PRIORITY_COMPETITIONS + SECONDARY_COMPETITIONS


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed": [], "requests_today": 0, "last_reset": str(date.today())}


def save_checkpoint(cp: dict):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(cp, f, indent=2)


def get_or_create_season(db, competition_id: int, year: int, fixtures: list) -> Season:
    """Récupère ou crée une saison."""
    season = db.execute(
        select(Season).where(
            Season.competition_id == competition_id,
            Season.year == year
        )
    ).scalar_one_or_none()

    if not season:
        # Calculer dates depuis les fixtures
        dates = [f["fixture"]["date"][:10] for f in fixtures if f.get("fixture", {}).get("date")]
        start = min(dates) if dates else f"{year}-07-01"
        end   = max(dates) if dates else f"{year+1}-06-30"
        is_current = (year == 2024)  # saison 2024/25 = courante

        season = Season(
            competition_id=competition_id,
            year=year,
            start_date=datetime.strptime(start, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end, "%Y-%m-%d").date(),
            is_current=is_current,
        )
        db.add(season)
        db.flush()
        logger.info("Season creee : comp=%d year=%d", competition_id, year)

    return season


def get_or_create_team(db, team_data: dict, competition_id: int) -> Team | None:
    """Récupère ou crée une équipe."""
    if not team_data or not team_data.get("id"):
        return None

    api_id = team_data["id"]
    team = db.execute(
        select(Team).where(Team.api_football_id == api_id)
    ).scalar_one_or_none()

    if not team:
        team = Team(
            api_football_id=api_id,
            name=team_data.get("name", "Unknown"),
            crest_url=team_data.get("logo"),
            competition_id=competition_id,
        )
        db.add(team)
        db.flush()

    return team


def import_fixtures(db, comp_code: str, api_comp_id: int, season_year: int) -> tuple[int, int]:
    """Importe les fixtures d'une competition/saison.
    
    Returns:
        Tuple (nb_created, nb_updated)
    """
    logger.info("Import fixtures %s saison %d...", comp_code, season_year)

    result = api_football_client._get("/fixtures", {
        "league": api_comp_id,
        "season": season_year,
    })
    fixtures = result.get("response", [])
    logger.info("  %d fixtures recuperees", len(fixtures))

    if not fixtures:
        return 0, 0

    # Récupérer la competition en BDD
    comp = db.execute(
        select(Competition).where(Competition.code == comp_code)
    ).scalar_one_or_none()
    if not comp:
        logger.warning("Competition %s introuvable en BDD", comp_code)
        return 0, 0

    # Créer/récupérer la saison
    season = get_or_create_season(db, comp.id, season_year, fixtures)

    created = updated = 0

    for f in fixtures:
        fix    = f.get("fixture", {})
        teams  = f.get("teams", {})
        goals  = f.get("goals", {})
        league = f.get("league", {})

        api_fix_id = fix.get("id")
        if not api_fix_id:
            continue

        # Statut api-football -> notre format
        status_map = {
            "FT": "FINISHED", "AET": "FINISHED", "PEN": "FINISHED",
            "NS": "SCHEDULED", "TBD": "TIMED", "LIVE": "LIVE",
            "1H": "LIVE", "2H": "LIVE", "HT": "LIVE",
            "PST": "POSTPONED", "CANC": "CANCELLED", "ABD": "CANCELLED",
        }
        raw_status = fix.get("status", {}).get("short", "NS")
        status = status_map.get(raw_status, "SCHEDULED")

        # Teams
        home_data = teams.get("home", {})
        away_data = teams.get("away", {})
        home_team = get_or_create_team(db, home_data, comp.id)
        away_team = get_or_create_team(db, away_data, comp.id)

        # Match date
        fix_date = fix.get("date")
        if fix_date:
            match_date = datetime.fromisoformat(fix_date.replace("Z", "+00:00"))
        else:
            continue

        # Chercher match existant
        match = db.execute(
            select(Match).where(Match.api_football_id == api_fix_id)
        ).scalar_one_or_none()

        if match:
            # Mise a jour
            match.status     = status
            match.home_score = goals.get("home")
            match.away_score = goals.get("away")
            match.round      = league.get("round")
            match.season_id  = season.id
            updated += 1
        else:
            match = Match(
                api_football_id=api_fix_id,
                competition_id=comp.id,
                season_id=season.id,
                home_team_id=home_team.id if home_team else None,
                away_team_id=away_team.id if away_team else None,
                match_date=match_date,
                status=status,
                home_score=goals.get("home"),
                away_score=goals.get("away"),
                matchday=None,  # calcule separement si besoin
                round=league.get("round"),
                venue=fix.get("venue", {}).get("name"),
                referee=fix.get("referee"),
            )
            db.add(match)
            created += 1

    db.commit()
    logger.info("  %s %d : %d crees, %d mis a jour", comp_code, season_year, created, updated)
    return created, updated


def import_stats_for_season(db, comp_code: str, api_comp_id: int, season_year: int, cp: dict, daily_limit: int = 7000) -> int:
    """Importe les stats pour tous les matchs FINISHED d'une saison.
    
    Returns:
        Nombre de requetes utilisees
    """
    comp = db.execute(select(Competition).where(Competition.code == comp_code)).scalar_one_or_none()
    if not comp:
        return 0

    # Matchs FINISHED sans stats
    from app.models.match_stat import MatchStat
    from sqlalchemy import outerjoin

    matches = db.execute(
        select(Match)
        .outerjoin(Match.match_stats)
        .where(Match.competition_id == comp.id)
        .where(Match.status == "FINISHED")
        .where(Match.api_football_id.isnot(None))
        .where(MatchStat.id == None)
        .order_by(Match.match_date)
    ).scalars().all()

    logger.info("  %d matchs sans stats pour %s %d", len(matches), comp_code, season_year)
    req_used = 0

    for match in matches:
        if cp["requests_today"] >= daily_limit:
            logger.warning("Quota journalier atteint (%d req), arret.", daily_limit)
            save_checkpoint(cp)
            return req_used

        key = f"stats_{match.api_football_id}"
        if key in cp["completed"]:
            continue

        try:
            stats = api_football_client.get_fixture_stats(match.api_football_id)
            cp["requests_today"] += 1
            req_used += 1

            for team_data in stats:
                team_api_id = team_data.get("team", {}).get("id")
                team = db.execute(select(Team).where(Team.api_football_id == team_api_id)).scalar_one_or_none()
                if not team:
                    continue

                side = "home" if team.id == match.home_team_id else "away"
                stat_dict = {s["type"]: s["value"] for s in team_data.get("statistics", [])}

                def parse_pct(val):
                    if val is None:
                        return None
                    if isinstance(val, str):
                        return float(val.replace("%", "")) if val else None
                    return float(val)

                ms = MatchStat(
                    match_id=match.id,
                    team_id=team.id,
                    side=side,
                    shots_total=stat_dict.get("Total Shots"),
                    shots_on_goal=stat_dict.get("Shots on Goal"),
                    shots_off_goal=stat_dict.get("Shots off Goal"),
                    shots_blocked=stat_dict.get("Blocked Shots"),
                    ball_possession=parse_pct(stat_dict.get("Ball Possession")),
                    passes_total=stat_dict.get("Total passes"),
                    passes_accurate=stat_dict.get("Passes accurate"),
                    passes_pct=parse_pct(stat_dict.get("Passes %")),
                    corner_kicks=stat_dict.get("Corner Kicks"),
                    fouls=stat_dict.get("Fouls"),
                    offsides=stat_dict.get("Offsides"),
                    yellow_cards=stat_dict.get("Yellow Cards"),
                    red_cards=stat_dict.get("Red Cards"),
                    goalkeeper_saves=stat_dict.get("Goalkeeper Saves"),
                    expected_goals=stat_dict.get("expected_goals") or stat_dict.get("Expected Goals"),
                    api_football_fixture_id=match.api_football_id,
                )
                db.add(ms)

            db.commit()
            cp["completed"].append(key)

        except Exception as e:
            logger.error("Erreur stats fixture %d : %s", match.api_football_id, e)
            db.rollback()

        # Pause pour respecter le rate limit api-football (10 req/s)
        time.sleep(0.15)

    save_checkpoint(cp)
    return req_used


def run_import(mode: str = "fixtures"):
    """Lance l'import.
    
    Args:
        mode: "fixtures" | "stats" | "all"
    """
    cp = load_checkpoint()

    # Reset quota si nouveau jour
    today = str(date.today())
    if cp.get("last_reset") != today:
        cp["requests_today"] = 0
        cp["last_reset"] = today
        logger.info("Nouveau jour — quota remis a zero")

    logger.info("Debut import mode=%s | req_today=%d", mode, cp["requests_today"])

    db = SessionLocal()
    total_req = 0

    try:
        for comp_code, api_comp_id in ALL_COMPETITIONS:
            for season_year in SEASONS:
                key = f"fixtures_{comp_code}_{season_year}"

                if mode in ("fixtures", "all"):
                    if key not in cp["completed"]:
                        created, updated = import_fixtures(db, comp_code, api_comp_id, season_year)
                        cp["completed"].append(key)
                        cp["requests_today"] += 1
                        total_req += 1
                        save_checkpoint(cp)
                        time.sleep(0.2)

                if mode in ("stats", "all"):
                    req = import_stats_for_season(db, comp_code, api_comp_id, season_year, cp)
                    total_req += req
                    if cp["requests_today"] >= 7000:
                        logger.warning("Quota atteint, reprise demain.")
                        break

    finally:
        db.close()

    logger.info("Import termine — %d requetes utilisees aujourd'hui", cp["requests_today"])
    return total_req


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "fixtures"
    print(f"Mode : {mode}")
    print("Modes disponibles : fixtures | stats | all")
    run_import(mode)