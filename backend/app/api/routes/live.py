"""Routes live scores (Phase 4E)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.match import MatchListItemOut
from app.services.live_service import fetch_live_scores, get_live_matches, get_todays_matches

router = APIRouter(tags=["live"])


@router.get("/live", response_model=list[MatchListItemOut])
def get_live(db: Session = Depends(get_db)) -> list:
    """Retourne les matchs actuellement en cours (IN_PLAY)."""
    return get_live_matches(db)


@router.get("/live/today", response_model=list[MatchListItemOut])
def get_today(db: Session = Depends(get_db)) -> list:
    """Retourne tous les matchs du jour."""
    return get_todays_matches(db)


@router.post("/live/refresh")
def refresh_live(db: Session = Depends(get_db)) -> dict:
    """Force la mise a jour des scores live depuis api-football.
    A appeler depuis le frontend toutes les 60-90 secondes.
    """
    result = fetch_live_scores(db)
    return {
        "status":        "ok",
        "updated":       result["updated"],
        "live_count":    len(result["live_matches"]),
        "live_matches":  result["live_matches"],
    }
