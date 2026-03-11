"""Route for the Smart Ticket generator (POST /smart-ticket)."""
import logging
from functools import reduce
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.smart_ticket import SmartTicket
from app.schemas.smart_ticket import (
    DISCLAIMER,
    SelectionItem,
    SmartTicketOut,
    SmartTicketRequest,
)
from app.services.prediction_service import prediction_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["smart-ticket"])

# ── Configuration constants ───────────────────────────────────────────────────

SEUIL_MIN_PROBA: float = 0.60
MAX_SELECTIONS: int = 3

# Map bet_type → (Prediction attribute name, display label)
_CANDIDATE_TYPES: dict[str, tuple[str, str]] = {
    "home_win":  ("home_win_proba",  "1X2 : Domicile gagne"),
    "draw":      ("draw_proba",      "1X2 : Match nul"),
    "away_win":  ("away_win_proba",  "1X2 : Extérieur gagne"),
    "btts_yes":  ("btts_proba",      "BTTS : Les deux marquent"),
    "over_15":   ("over_15_proba",   "Over 1.5 buts"),
    "over_25":   ("over_25_proba",   "Over 2.5 buts"),
    "home_draw": ("home_draw_proba", "Chance double : 1X"),
    "away_draw": ("away_draw_proba", "Chance double : X2"),
    "home_away": ("home_away_proba", "Chance double : 12"),
}

# Paires corrélées : ne pas combiner sur le même match
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
           - In "simple" mode: only one selection per match.
        4. Compute combined probability as the product of selected probabilities.
        5. Persist the ticket in DB.
        6. Return ticket with selections, combined proba, confidence and disclaimer.

    Raises:
        422: If a match is missing, or no valid selections are found.
    """
    candidates: list[SelectionItem] = []
    confidence_scores: list[int] = []
    first_pred_id: Optional[int] = None

    # ── Step 1 & 2: collect candidate bets ───────────────────────────────────
    for match_id in request.match_ids:
        try:
            pred, _ = prediction_service.get_or_create_prediction(match_id, db)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Match {match_id} : {exc}",
            )

        # Garder l'ID de la première prédiction pour la FK du ticket
        if first_pred_id is None:
            first_pred_id = pred.id

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

    # ── Step 3: greedy selection ──────────────────────────────────────────────
    candidates.sort(key=lambda c: c.probability, reverse=True)

    selected: list[SelectionItem] = []
    correlated_warning: Optional[str] = None
    seen_matches: set[int] = set()

    for cand in candidates:
        if len(selected) >= MAX_SELECTIONS:
            break

        # Mode "simple" : une seule sélection par match
        if request.mode == "simple" and cand.match_id in seen_matches:
            continue

        # Vérification des corrélations intra-match
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
            seen_matches.add(cand.match_id)

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

    # ── Step 5: persist in DB ─────────────────────────────────────────────────
    ticket_orm = SmartTicket(
        match_id=request.match_ids[0],
        prediction_id=first_pred_id,
        selections=[s.model_dump() for s in selected],
        combined_proba=combined_proba,
        confidence_score=confidence_score,
        mode=request.mode,
    )
    db.add(ticket_orm)
    db.commit()
    db.refresh(ticket_orm)
    logger.info(
        "Smart Ticket créé id=%d | %d sélections | combined_proba=%.3f",
        ticket_orm.id,
        len(selected),
        combined_proba,
    )

    # ── Step 6: return response ───────────────────────────────────────────────
    return SmartTicketOut(
        id=ticket_orm.id,
        match_id=ticket_orm.match_id,
        prediction_id=ticket_orm.prediction_id,
        selections=selected,
        combined_proba=combined_proba,
        confidence_score=confidence_score,
        mode=request.mode,
        correlated_warning=correlated_warning,
        disclaimer=DISCLAIMER,
    )
