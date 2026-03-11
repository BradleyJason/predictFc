"""Route for the Smart Ticket generator (POST /smart-ticket)."""
from functools import reduce
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.smart_ticket import (
    DISCLAIMER,
    SelectionItem,
    SmartTicketOut,
    SmartTicketRequest,
)
from app.services.prediction_service import prediction_service

router = APIRouter(tags=["smart-ticket"])

# ── Configuration constants ───────────────────────────────────────────────────

SEUIL_MIN_PROBA: float = 0.60   # minimum probability per selection
MAX_SELECTIONS: int = 3          # maximum selections in one ticket

# Map bet_type → (Prediction attribute name, display label)
_CANDIDATE_TYPES: dict[str, tuple[str, str]] = {
    "home_win":  ("home_win_proba",  "1X2 : Domicile gagne"),
    "draw":      ("draw_proba",      "1X2 : Match nul"),
    "away_win":  ("away_win_proba",  "1X2 : Extérieur gagne"),
    "btts_yes":  ("btts_proba",      "BTTS : Les deux marquent"),
    "over_25":   ("over_25_proba",   "Over 2.5 buts"),
    "home_draw": ("home_draw_proba", "Chance double : 1X"),
    "away_draw": ("away_draw_proba", "Chance double : X2"),
    "home_away": ("home_away_proba", "Chance double : 12"),
}

# Pairs of bet types that are too correlated to combine (same match)
_CORRELATED_PAIRS: list[frozenset] = [
    frozenset({"over_25",  "btts_yes"}),
    frozenset({"home_win", "home_draw"}),
    frozenset({"away_win", "away_draw"}),
    frozenset({"draw",     "home_draw"}),
    frozenset({"draw",     "away_draw"}),
]


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/smart-ticket", response_model=SmartTicketOut)
def generate_smart_ticket(
    request: SmartTicketRequest,
    db: Session = Depends(get_db),
) -> SmartTicketOut:
    """Generate an optimised combined ticket for the requested matches.

    Algorithm:
        1. Get or create a prediction for each match_id.
        2. Build a list of all bet candidates (probability ≥ 60 %).
        3. Sort by probability (desc) and greedily select up to 3:
           - Skip bets correlated with an already-selected bet on the same match.
        4. Compute combined probability as the product of selected probabilities.
        5. Return ticket with selections, combined proba, confidence and disclaimer.

    Raises:
        422: If a match is missing, or no valid selections are found.
    """
    candidates: list[SelectionItem] = []
    confidence_scores: list[int] = []

    # ── Step 1 & 2: collect candidate bets ────────────────────────────────────
    for match_id in request.match_ids:
        try:
            pred, _ = prediction_service.get_or_create_prediction(match_id, db)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Match {match_id} : {exc}",
            )

        if pred.confidence_score is not None:
            confidence_scores.append(pred.confidence_score)

        for bet_type, (attr, label) in _CANDIDATE_TYPES.items():
            value: Optional[float] = getattr(pred, attr, None)
            if value is not None and value >= SEUIL_MIN_PROBA:
                candidates.append(
                    SelectionItem(
                        match_id=match_id,
                        bet_type=bet_type,
                        label=label,
                        probability=value,
                    )
                )

    # ── Step 3: greedy selection ───────────────────────────────────────────────
    candidates.sort(key=lambda c: c.probability, reverse=True)

    selected: list[SelectionItem] = []
    correlated_warning: Optional[str] = None

    for cand in candidates:
        if len(selected) >= MAX_SELECTIONS:
            break

        # Check for correlation with already-selected bets on the same match
        is_correlated = False
        for already in selected:
            if already.match_id == cand.match_id:
                pair = frozenset({already.bet_type, cand.bet_type})
                if pair in _CORRELATED_PAIRS:
                    is_correlated = True
                    correlated_warning = (
                        f"Paris corrélés détectés ({already.bet_type} / {cand.bet_type}) "
                        "— sélection ajustée pour optimiser la combinaison."
                    )
                    break

        if not is_correlated:
            selected.append(cand)

    if not selected:
        raise HTTPException(
            status_code=422,
            detail=(
                "Aucune sélection disponible avec le seuil actuel (min 60 %). "
                "Vérifiez que le modèle a été entraîné sur ces matchs."
            ),
        )

    # ── Step 4: compute combined metrics ─────────────────────────────────────
    combined_proba: float = reduce(
        lambda acc, sel: acc * sel.probability, selected, 1.0
    )
    confidence_score: int = (
        int(sum(confidence_scores) / len(confidence_scores))
        if confidence_scores
        else 50
    )

    return SmartTicketOut(
        selections=selected,
        combined_proba=combined_proba,
        confidence_score=confidence_score,
        mode=request.mode,
        correlated_warning=correlated_warning,
        disclaimer=DISCLAIMER,
    )
