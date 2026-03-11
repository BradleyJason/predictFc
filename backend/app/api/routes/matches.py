"""Routes FastAPI — matchs.

GET /matches          — liste filtrée et paginée
GET /matches/{id}     — détail d'un match avec équipes
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.match import Match
from app.schemas.match import MatchListOut, MatchOut

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListOut)
def list_matches(
    competition_id: int | None = Query(None, description="Filtrer par compétition"),
    status: str | None = Query(None, description="SCHEDULED | IN_PLAY | FINISHED"),
    date_from: date | None = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="Date de fin (YYYY-MM-DD)"),
    matchday: int | None = Query(None, description="Numéro de journée"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> MatchListOut:
    """Retourne la liste des matchs avec filtres optionnels.

    Args:
        competition_id: Filtre sur la compétition.
        status: Filtre sur le statut (SCHEDULED, IN_PLAY, FINISHED).
        date_from: Borne inférieure de date du match.
        date_to: Borne supérieure de date du match.
        matchday: Filtre sur la journée.
        skip: Offset de pagination.
        limit: Nombre maximum de résultats.
        db: Session BDD injectée.

    Returns:
        Liste paginée de matchs avec total.
    """
    q = db.query(Match).options(
        joinedload(Match.home_team),
        joinedload(Match.away_team),
    )

    if competition_id is not None:
        q = q.filter(Match.competition_id == competition_id)
    if status is not None:
        q = q.filter(Match.status == status.upper())
    if date_from is not None:
        q = q.filter(Match.match_date >= date_from)
    if date_to is not None:
        q = q.filter(Match.match_date <= date_to)
    if matchday is not None:
        q = q.filter(Match.matchday == matchday)

    total = q.count()
    matches = q.order_by(Match.match_date.desc()).offset(skip).limit(limit).all()

    return MatchListOut(matches=matches, total=total, skip=skip, limit=limit)


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)) -> MatchOut:
    """Retourne le détail d'un match avec ses équipes.

    Args:
        match_id: ID interne du match.
        db: Session BDD injectée.

    Returns:
        Match complet avec home_team et away_team.

    Raises:
        HTTPException 404: Si le match n'existe pas.
    """
    match = (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")
    return match
