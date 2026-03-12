"""Routes compositions (Phase 4D)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.lineup_service import (
    import_lineups_for_match,
    get_lineups_for_match,
    compute_formation_factor,
)

router = APIRouter(tags=["lineups"])


class LineupPlayerOut(BaseModel):
    id: int
    player_name: Optional[str] = None
    number: Optional[int] = None
    position: Optional[str] = None
    grid: Optional[str] = None
    is_starter: bool = True
    model_config = {"from_attributes": True}


class LineupOut(BaseModel):
    id: int
    team_id: int
    formation: Optional[str] = None
    coach_name: Optional[str] = None
    players: list[LineupPlayerOut] = []
    model_config = {"from_attributes": True}


class LineupsMatchOut(BaseModel):
    match_id: int
    lineups: list[LineupOut]
    factor_home: float
    factor_away: float


@router.get("/lineups/match/{match_id}", response_model=LineupsMatchOut)
def get_match_lineups(match_id: int, db: Session = Depends(get_db)) -> LineupsMatchOut:
    """Retourne les compositions et facteurs tactiques pour un match."""
    from app.models.match import Match
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")

    lineups = get_lineups_for_match(match_id, db)
    fh, fa = compute_formation_factor(
        match.home_team_id, match.away_team_id, match_id, db
    )
    return LineupsMatchOut(
        match_id=match_id,
        lineups=lineups,
        factor_home=fh,
        factor_away=fa,
    )


@router.post("/lineups/import/{match_id}")
def import_match_lineups(match_id: int, db: Session = Depends(get_db)) -> dict:
    """Importe les compositions depuis api-football."""
    try:
        count = import_lineups_for_match(match_id, db)
        return {"status": "ok", "match_id": match_id, "lineups_imported": count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
