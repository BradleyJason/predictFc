"""Routes Value Bet Detector (Phase 4F)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.value_bet_service import (
    detect_value_bets,
    scan_upcoming_value_bets,
    VALUE_BET_THRESHOLD,
    VALUE_BET_STRONG,
)

router = APIRouter(tags=["value-bets"])


class ValueBetOut(BaseModel):
    match_id:      int
    market:        str
    model_proba:   float
    implied_proba: float
    odd:           float
    value:         float
    expected_roi:  float
    bookmaker:     str
    strength:      str
    match_date:    Optional[str] = None
    home_team:     Optional[str] = None
    away_team:     Optional[str] = None
    competition:   Optional[str] = None


@router.get("/value-bets/match/{match_id}", response_model=list[ValueBetOut])
def get_match_value_bets(match_id: int, db: Session = Depends(get_db)) -> list:
    """Detecte les value bets pour un match specifique.

    Necessite : prediction + cotes en BDD.
    Retourne les bets avec value > 5% tries par value decroissante.
    """
    bets = detect_value_bets(match_id, db)
    return [b.to_dict() for b in bets]


@router.get("/value-bets", response_model=list[ValueBetOut])
def get_all_value_bets(
    min_value: float = Query(VALUE_BET_THRESHOLD, ge=0.0, le=1.0,
                             description="Valeur minimum (defaut 5%)"),
    strong_only: bool = Query(False, description="Seulement les value bets fortes (>10%)"),
    db: Session = Depends(get_db),
) -> list:
    """Scanne tous les matchs a venir et retourne les value bets.

    Filtre par min_value ou strong_only.
    Trie par value decroissante — les meilleures opportunites en premier.
    """
    threshold = VALUE_BET_STRONG if strong_only else min_value
    return scan_upcoming_value_bets(db, min_value=threshold)


@router.get("/value-bets/summary")
def get_value_bets_summary(db: Session = Depends(get_db)) -> dict:
    """Resume statistique des value bets disponibles."""
    all_bets = scan_upcoming_value_bets(db)
    strong   = [b for b in all_bets if b["strength"] == "strong"]
    normal   = [b for b in all_bets if b["strength"] == "normal"]

    avg_roi = sum(b["expected_roi"] for b in all_bets) / len(all_bets) if all_bets else 0

    markets = {}
    for b in all_bets:
        markets[b["market"]] = markets.get(b["market"], 0) + 1

    return {
        "total":        len(all_bets),
        "strong":       len(strong),
        "normal":       len(normal),
        "avg_roi":      round(avg_roi, 2),
        "by_market":    markets,
        "threshold":    VALUE_BET_THRESHOLD,
    }
