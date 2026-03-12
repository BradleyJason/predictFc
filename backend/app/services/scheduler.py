"""Scheduler APScheduler — enrichissement automatique nuitier.

Taches planifiees :
  - 03h00 : import fixtures J+7 (matchs a venir)
  - 03h15 : import stats matchs termines hier/avant-hier
  - 03h30 : invalidation cache modele ML
"""
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Taches
# ---------------------------------------------------------------------------

def task_import_upcoming_fixtures() -> None:
    """Importe les fixtures des 7 prochains jours pour toutes les competitions actives."""
    logger.info("[Scheduler] Debut import fixtures a venir...")
    try:
        from app.core.database import SessionLocal
        from app.models.competition import Competition
        from app.models.season import Season
        from app.services.import_history import (
            get_or_create_season,
            get_or_create_team,
            api_football_client,
        )
        from app.models.match import Match
        from sqlalchemy import select

        db = SessionLocal()
        try:
            today = datetime.now(timezone.utc).date()
            date_to = today + timedelta(days=7)

            active_comps = db.execute(
                select(Competition).where(
                    Competition.is_active == True,
                    Competition.api_football_id.is_not(None),
                )
            ).scalars().all()

            total_created = total_updated = 0

            for comp in active_comps:
                season = db.execute(
                    select(Season).where(
                        Season.competition_id == comp.id,
                        Season.is_current == True,
                    )
                ).scalar_one_or_none()

                if not season:
                    continue

                try:
                    data = api_football_client.get(
                        "fixtures",
                        league=comp.api_football_id,
                        season=season.year,
                        **{"from": str(today), "to": str(date_to)},
                    )
                    fixtures = data.get("response", [])
                    created = updated = 0

                    for fix in fixtures:
                        api_id = fix["fixture"]["id"]
                        existing = db.execute(
                            select(Match).where(Match.api_football_id == api_id)
                        ).scalar_one_or_none()

                        home = get_or_create_team(db, fix["teams"]["home"])
                        away = get_or_create_team(db, fix["teams"]["away"])

                        status_map = {
                            "FT": "FINISHED", "AET": "FINISHED", "PEN": "FINISHED",
                            "NS": "SCHEDULED", "TBD": "SCHEDULED",
                            "1H": "IN_PLAY", "HT": "IN_PLAY", "2H": "IN_PLAY",
                            "CANC": "CANCELLED", "PST": "POSTPONED",
                        }
                        short = fix["fixture"]["status"]["short"]
                        status = status_map.get(short, short)

                        dt_str = fix["fixture"]["date"]
                        from datetime import datetime as dt
                        match_date = dt.fromisoformat(dt_str.replace("Z", "+00:00"))

                        if existing:
                            existing.status     = status
                            existing.home_score = (fix["goals"]["home"])
                            existing.away_score = (fix["goals"]["away"])
                            updated += 1
                        else:
                            match = Match(
                                api_football_id = api_id,
                                competition_id  = comp.id,
                                season_id       = season.id,
                                home_team_id    = home.id,
                                away_team_id    = away.id,
                                match_date      = match_date,
                                status          = status,
                                home_score      = fix["goals"]["home"],
                                away_score      = fix["goals"]["away"],
                                round           = fix["league"].get("round"),
                                venue           = fix["fixture"].get("venue", {}).get("name"),
                                referee         = fix["fixture"].get("referee"),
                            )
                            db.add(match)
                            created += 1

                    db.commit()
                    total_created += created
                    total_updated += updated
                    if created or updated:
                        logger.info("  %s : %d crees, %d mis a jour", comp.code, created, updated)

                except Exception as exc:
                    logger.warning("Erreur fixtures %s : %s", comp.code, exc)
                    db.rollback()

            logger.info(
                "[Scheduler] Fixtures terminees : %d crees, %d mis a jour",
                total_created, total_updated,
            )
        finally:
            db.close()

    except Exception as exc:
        logger.error("[Scheduler] Erreur task_import_upcoming_fixtures : %s", exc)


def task_import_recent_stats() -> None:
    """Importe les stats des matchs termines hier et avant-hier sans stats."""
    logger.info("[Scheduler] Debut import stats recentes...")
    try:
        from app.core.database import SessionLocal
        from app.models.match import Match
        from app.models.match_stat import MatchStat
        from app.services.import_history import api_football_client, import_stats_for_season
        from sqlalchemy import select

        db = SessionLocal()
        try:
            today = datetime.now(timezone.utc).date()
            date_from = today - timedelta(days=2)

            # Matchs termines recemment sans stats
            matches = db.execute(
                select(Match)
                .outerjoin(MatchStat, MatchStat.match_id == Match.id)
                .where(
                    Match.status == "FINISHED",
                    Match.api_football_id.is_not(None),
                    Match.match_date >= date_from,
                    MatchStat.id.is_(None),
                )
                .order_by(Match.match_date.desc())
            ).scalars().all()

            logger.info("  %d matchs sans stats a enrichir", len(matches))
            total = 0

            for match in matches:
                try:
                    data = api_football_client.get(
                        "fixtures/statistics",
                        fixture=match.api_football_id,
                    )
                    stats = data.get("response", [])
                    if not stats:
                        continue

                    # Parser et inserer les stats
                    for side_data in stats:
                        team_side = side_data.get("team", {})
                        # Determiner HOME ou AWAY
                        from app.models.team import Team
                        team = db.execute(
                            select(Team).where(
                                Team.api_football_id == team_side.get("id")
                            )
                        ).scalar_one_or_none()
                        if not team:
                            continue

                        side = "HOME" if team.id == match.home_team_id else "AWAY"

                        def val(stats_list, key):
                            for s in stats_list:
                                if s["type"] == key:
                                    v = s["value"]
                                    return None if v in (None, "None") else v
                            return None

                        st = side_data.get("statistics", [])
                        stat = MatchStat(
                            match_id          = match.id,
                            side              = side,
                            shots_total       = val(st, "Total Shots"),
                            shots_on_goal     = val(st, "Shots on Goal"),
                            shots_off_goal    = val(st, "Shots off Goal"),
                            shots_blocked     = val(st, "Blocked Shots"),
                            ball_possession   = float(str(val(st, "Ball Possession") or "0").replace("%","") or 0) or None,
                            passes_total      = val(st, "Total passes"),
                            passes_accurate   = val(st, "Passes accurate"),
                            corner_kicks      = val(st, "Corner Kicks"),
                            fouls             = val(st, "Fouls"),
                            offsides          = val(st, "Offsides"),
                            yellow_cards      = val(st, "Yellow Cards"),
                            red_cards         = val(st, "Red Cards"),
                            goalkeeper_saves  = val(st, "Goalkeeper Saves"),
                            expected_goals    = val(st, "expected_goals"),
                        )
                        db.add(stat)

                    total += 1

                except Exception as exc:
                    logger.warning(
                        "Erreur stats match %d : %s", match.id, exc
                    )

            db.commit()
            logger.info("[Scheduler] Stats terminees : %d matchs enrichis", total)

        finally:
            db.close()

    except Exception as exc:
        logger.error("[Scheduler] Erreur task_import_recent_stats : %s", exc)


def task_invalidate_model_cache() -> None:
    """Invalide le cache ML pour forcer le rechargement avec les nouvelles donnees."""
    logger.info("[Scheduler] Invalidation cache modele ML...")
    try:
        from app.services.prediction_service import invalidate_model
        invalidate_model()
        logger.info("[Scheduler] Cache modele invalide OK")
    except Exception as exc:
        logger.error("[Scheduler] Erreur invalidation cache : %s", exc)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def create_scheduler() -> BackgroundScheduler:
    """Cree et configure le scheduler avec les 3 taches nuitieres."""
    scheduler = BackgroundScheduler(timezone="Europe/Paris")

    scheduler.add_job(
        task_import_upcoming_fixtures,
        trigger=CronTrigger(hour=3, minute=0),
        id="import_upcoming_fixtures",
        name="Import fixtures J+7",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        task_import_recent_stats,
        trigger=CronTrigger(hour=3, minute=15),
        id="import_recent_stats",
        name="Import stats recentes",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        task_invalidate_model_cache,
        trigger=CronTrigger(hour=3, minute=30),
        id="invalidate_model_cache",
        name="Invalidation cache ML",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    return scheduler
