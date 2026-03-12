"""Routes cotes bookmakers (Phase 4C)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.odds_service import (
    import_odds_for_match,
    get_odds_for_match,
    odds_to_probas,
)

router = APIRouter(tags=["odds"])


class OddsOut(BaseModel):
    id: int
    bookmaker_name: Optional[str] = None
    home_win: Optional[float] = None
    draw: Optional[float] = None
    away_win: Optional[float] = None
    over_25: Optional[float] = None
    under_25: Optional[float] = None
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None
    model_config = {"from_attributes": True}


class OddsMatchOut(BaseModel):
    match_id: int
    odds: list[OddsOut]
    implied_home_win: Optional[float] = None
    implied_draw: Optional[float] = None
    implied_away_win: Optional[float] = None
    bookmaker_margin: Optional[float] = None


@router.get("/odds/match/{match_id}", response_model=OddsMatchOut)
def get_match_odds(match_id: int, db: Session = Depends(get_db)) -> OddsMatchOut:
    """Retourne les cotes et probabilites implicites pour un match."""
    odds = get_odds_for_match(match_id, db)
    probas = odds_to_probas(odds) if odds else {}
    return OddsMatchOut(
        match_id=match_id,
        odds=odds,
        implied_home_win=probas.get("home_win"),
        implied_draw=probas.get("draw"),
        implied_away_win=probas.get("away_win"),
        bookmaker_margin=probas.get("margin"),
    )


@router.post("/odds/import/{match_id}")
def import_match_odds(match_id: int, db: Session = Depends(get_db)) -> dict:
    """Importe les cotes depuis api-football pour un match specifique."""
    try:
        count = import_odds_for_match(match_id, db)
        return {"status": "ok", "match_id": match_id, "odds_imported": count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
