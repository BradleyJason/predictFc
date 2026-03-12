"""Routes blessures/suspensions (Phase 4B)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.injury_service import (
    import_injuries_for_match,
    get_injuries_for_match,
    compute_injury_penalty,
)

router = APIRouter(tags=["injuries"])


class InjuryOut(BaseModel):
    id: int
    player_name: Optional[str] = None
    player_api_id: Optional[int] = None
    injury_type: Optional[str] = None
    reason: Optional[str] = None
    team_id: int
    model_config = {"from_attributes": True}


class InjuriesMatchOut(BaseModel):
    match_id: int
    home_injuries: list[InjuryOut]
    away_injuries: list[InjuryOut]
    penalty_home: float
    penalty_away: float


@router.get("/injuries/match/{match_id}", response_model=InjuriesMatchOut)
def get_match_injuries(match_id: int, db: Session = Depends(get_db)) -> InjuriesMatchOut:
    """Retourne les blessures/suspensions pour un match avec les penalites calculees."""
    from app.models.match import Match
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")

    injuries = get_injuries_for_match(match_id, db)
    ph, pa = compute_injury_penalty(match.home_team_id, match.away_team_id, match_id, db)

    home_inj = [i for i in injuries if i.team_id == match.home_team_id]
    away_inj = [i for i in injuries if i.team_id == match.away_team_id]

    return InjuriesMatchOut(
        match_id=match_id,
        home_injuries=home_inj,
        away_injuries=away_inj,
        penalty_home=ph,
        penalty_away=pa,
    )


@router.post("/injuries/import/{match_id}")
def import_match_injuries(match_id: int, db: Session = Depends(get_db)) -> dict:
    """Importe les blessures depuis api-football pour un match specifique."""
    try:
        count = import_injuries_for_match(match_id, db)
        return {"status": "ok", "match_id": match_id, "injuries_imported": count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
