"""Routes for match listing and detail."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.match import Match
from app.schemas.match import MatchListOut, MatchOut

router = APIRouter(tags=["matches"])


@router.get("/matches", response_model=MatchListOut)
def list_matches(
    from fastapi import APIRouter, Depends, HTTPException, Query

    competition_id: Optional[int] = Query(None, description="Filtrer par compétition"),
    status: Optional[str] = Query(None, description="SCHEDULED | IN_PLAY | FINISHED"),
    date_from: Optional[date] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    matchday: Optional[int] = Query(None, description="Numéro de journée"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> MatchListOut:
    """Return a paginated list of matches with optional filters.

    Query params:
        competition_id: Filter by competition FK.
        status:         Filter by status string (e.g. SCHEDULED, FINISHED).
        date_from:      Lower bound on match_date (inclusive).
        date_to:        Upper bound on match_date (inclusive).
        matchday:       Filter by matchday number.
        skip / limit:   Pagination.
    """
    base_query = (
        select(Match)
        .options(
            joinedload(Match.competition),
            joinedload(Match.home_team),
            joinedload(Match.away_team),
        )
        .order_by(Match.match_date.desc())
    )

    if competition_id is not None:
        base_query = base_query.where(Match.competition_id == competition_id)
    if status:
        base_query = base_query.where(Match.status == status.upper())
    if date_from:
        base_query = base_query.where(Match.match_date >= date_from)
    if date_to:
        base_query = base_query.where(Match.match_date <= date_to)
    if matchday is not None:
        base_query = base_query.where(Match.matchday == matchday)

    total: int = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0

    matches = db.scalars(base_query.offset(skip).limit(limit)).all()

    return MatchListOut(
        matches=list(matches),
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)) -> Match:
    """Return a single match by ID, with competition and team details."""
    match = db.scalar(
        select(Match)
        .options(
            joinedload(Match.competition),
            joinedload(Match.home_team),
            joinedload(Match.away_team),
        )
        .where(Match.id == match_id)
    )
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")
    return match
