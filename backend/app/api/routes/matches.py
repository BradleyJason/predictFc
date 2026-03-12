"""Routes for match listing and detail."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.core.database import get_db
from app.models.match import Match
from app.schemas.match import MatchListItemOut, MatchListOut, MatchOut

router = APIRouter(tags=["matches"])


def _base_options():
    return [
        joinedload(Match.competition),
        joinedload(Match.home_team),
        joinedload(Match.away_team),
    ]


@router.get("/matches", response_model=MatchListOut)
def list_matches(
    competition_id: Optional[int] = Query(None),
    season_id: Optional[int] = Query(None, description="Filtrer par saison"),
    status: Optional[str] = Query(None, description="SCHEDULED | IN_PLAY | FINISHED"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    matchday: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> MatchListOut:
    """Liste paginee de matchs avec filtres optionnels."""
    q = select(Match).options(*_base_options()).order_by(Match.match_date.desc())

    if competition_id is not None:
        q = q.where(Match.competition_id == competition_id)
    if season_id is not None:
        q = q.where(Match.season_id == season_id)
    if status:
        q = q.where(Match.status == status.upper())
    if date_from:
        q = q.where(Match.match_date >= date_from)
    if date_to:
        q = q.where(Match.match_date <= date_to)
    if matchday is not None:
        q = q.where(Match.matchday == matchday)

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    matches = db.execute(q.offset(skip).limit(limit)).unique().scalars().all()

    return MatchListOut(matches=list(matches), total=total, skip=skip, limit=limit)


@router.get("/matches/by-api-id/{api_football_id}", response_model=MatchOut)
def get_match_by_api_id(api_football_id: int, db: Session = Depends(get_db)) -> Match:
    """Retourne un match par son api_football_id (id api-football.com)."""
    match = db.scalar(
        select(Match)
        .options(*_base_options(), selectinload(Match.match_stats))
        .where(Match.api_football_id == api_football_id)
    )
    if not match:
        raise HTTPException(status_code=404, detail=f"Match api_football_id={api_football_id} introuvable.")
    return match


@router.get("/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)) -> Match:
    """Retourne un match par son ID interne, avec stats."""
    match = db.scalar(
        select(Match)
        .options(*_base_options(), selectinload(Match.match_stats))
        .where(Match.id == match_id)
    )
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")
    return match


@router.get("/matches/{match_id}/match-stats")
def get_match_raw_stats(match_id: int, db: Session = Depends(get_db)):
    """Retourne les stats brutes (MatchStat) du match — possession, tirs, xG, etc."""
    from sqlalchemy import select
    from app.models.match_stat import MatchStat
    from app.models.team import Team

    rows = db.execute(
        select(MatchStat).where(MatchStat.match_id == match_id)
    ).scalars().all()

    if not rows:
        return {"match_id": match_id, "stats": []}

    result = []
    for r in rows:
        team = db.get(Team, r.team_id)
        result.append({
            "side":               r.side,
            "team_name":          team.name if team else None,
            "team_crest":         team.crest_url if team else None,
            "shots_total":        r.shots_total,
            "shots_on_goal":      r.shots_on_goal,
            "shots_off_goal":     r.shots_off_goal,
            "shots_blocked":      r.shots_blocked,
            "ball_possession":    r.ball_possession,
            "passes_total":       r.passes_total,
            "passes_accurate":    r.passes_accurate,
            "passes_pct":         r.passes_pct,
            "corner_kicks":       r.corner_kicks,
            "fouls":              r.fouls,
            "offsides":           r.offsides,
            "yellow_cards":       r.yellow_cards,
            "red_cards":          r.red_cards,
            "goalkeeper_saves":   r.goalkeeper_saves,
            "expected_goals":     r.expected_goals,
        })
    return {"match_id": match_id, "stats": result}
