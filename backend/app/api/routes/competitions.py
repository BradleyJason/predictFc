"""Routes competitions et teams (utilitaires frontend)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.competition import Competition
from app.models.team import Team

router = APIRouter(tags=["competitions", "teams"])


@router.get("/competitions")
def get_competitions(db: Session = Depends(get_db)) -> list:
    """Retourne toutes les competitions actives triees par nom."""
    comps = db.execute(
        select(Competition)
        .where(Competition.is_active == True)
        .order_by(Competition.name)
    ).scalars().all()
    return [
        {
            "id":              c.id,
            "name":            c.name,
            "code":            c.code,
            "type":            c.type,
            "country":         c.country,
            "crest_url":       c.crest_url,
            "api_football_id": c.api_football_id,
        }
        for c in comps
    ]


@router.get("/teams/search")
def search_teams(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
) -> list:
    """Recherche des equipes par nom (min 2 caracteres)."""
    pattern = f"%{q}%"
    teams = db.execute(
        select(Team)
        .where(
            or_(
                Team.name.ilike(pattern),
                Team.short_name.ilike(pattern),
            )
        )
        .order_by(Team.name)
        .limit(20)
    ).scalars().all()
    return [
        {
            "id":              t.id,
            "name":            t.name,
            "short_name":      t.short_name,
            "crest_url":       t.crest_url,
            "country":         t.country,
            "api_football_id": t.api_football_id,
        }
        for t in teams
    ]


@router.get("/teams/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)) -> dict:
    """Retourne les infos d une equipe."""
    from sqlalchemy.orm import joinedload
    from app.models.match import Match
    from app.utils.exceptions import NotFoundError
    team = db.get(Team, team_id)
    if not team:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Equipe {team_id} introuvable.")

    # 10 derniers matchs
    recent = db.execute(
        select(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition))
        .where(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == "FINISHED",
        )
        .order_by(Match.match_date.desc())
        .limit(10)
    ).unique().scalars().all()

    # Prochains matchs
    from datetime import datetime, timezone
    upcoming = db.execute(
        select(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team), joinedload(Match.competition))
        .where(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status.in_(["SCHEDULED", "TIMED"]),
            Match.match_date >= datetime.now(timezone.utc),
        )
        .order_by(Match.match_date)
        .limit(5)
    ).unique().scalars().all()

    def fmt_match(m):
        is_home = m.home_team_id == team_id
        opp     = m.away_team if is_home else m.home_team
        if m.status == "FINISHED":
            gs = m.home_score if is_home else m.away_score
            gc = m.away_score if is_home else m.home_score
            result = "W" if gs > gc else ("D" if gs == gc else "L")
        else:
            gs = gc = result = None
        return {
            "id":          m.id,
            "date":        m.match_date.isoformat() if m.match_date else None,
            "competition": m.competition.name if m.competition else None,
            "opponent":    {"id": opp.id, "name": opp.name, "short_name": opp.short_name, "crest_url": opp.crest_url} if opp else None,
            "is_home":     is_home,
            "goals_for":   gs,
            "goals_against": gc,
            "result":      result,
            "status":      m.status,
        }

    recent_fmt  = [fmt_match(m) for m in recent]
    wins   = sum(1 for m in recent_fmt if m["result"] == "W")
    draws  = sum(1 for m in recent_fmt if m["result"] == "D")
    losses = sum(1 for m in recent_fmt if m["result"] == "L")
    gf     = sum(m["goals_for"] or 0 for m in recent_fmt)
    ga     = sum(m["goals_against"] or 0 for m in recent_fmt)
    form   = [m["result"] for m in recent_fmt if m["result"]][:5]

    return {
        "id":              team.id,
        "name":            team.name,
        "short_name":      team.short_name,
        "crest_url":       team.crest_url,
        "country":         team.country,
        "venue_name":      team.venue_name,
        "api_football_id": team.api_football_id,
        "stats": {
            "played":       len(recent_fmt),
            "wins":         wins,
            "draws":        draws,
            "losses":       losses,
            "goals_for":    gf,
            "goals_against": ga,
            "form":         form,
        },
        "recent_matches":  recent_fmt,
        "upcoming_matches": [fmt_match(m) for m in upcoming],
    }
