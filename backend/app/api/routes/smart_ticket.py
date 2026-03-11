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

# ── Seuils ────────────────────────────────────────────────────────────────────
SEUIL_SAFE_MIN:  float = 0.60   # Smart Ticket : proba >= 60%
SEUIL_HOT_MIN:   float = 0.35   # Danger Zone  : proba 35-59%
SEUIL_HOT_MAX:   float = 0.59
MAX_SELECTIONS:  int   = 8

# ── Types de paris — (attribut sur Prediction, label affiché) ────────────────
# NB: over_05 et over_15 exclus volontairement (trop safe, cote inutile)
_CANDIDATE_TYPES: dict[str, tuple[str, str]] = {
    "home_win":  ("home_win_proba",  "Victoire domicile"),
    "draw":      ("draw_proba",      "Match nul"),
    "away_win":  ("away_win_proba",  "Victoire extérieur"),
    "btts_yes":  ("btts_proba",      "Les deux marquent"),
    "btts_no":   ("btts_proba",      "Les deux ne marquent pas"),
    "over_25":   ("over_25_proba",   "Plus de 2.5 buts"),
    "over_35":   ("over_35_proba",   "Plus de 3.5 buts"),
    "over_45":   ("over_45_proba",   "Plus de 4.5 buts"),
    "under_25":  ("over_25_proba",   "Moins de 2.5 buts"),
    "under_35":  ("over_35_proba",   "Moins de 3.5 buts"),
    "home_draw": ("home_draw_proba", "Chance double 1X"),
    "away_draw": ("away_draw_proba", "Chance double X2"),
    "home_away": ("home_away_proba", "Chance double 12"),
}

# Types dont on prend l'inverse (1 - proba)
_INVERSE_TYPES: set[str] = {"btts_no", "under_25", "under_35"}

# ── Corrélations complètes — jamais combiner ces paires sur le même match ─────
_CORRELATED_PAIRS: list[frozenset] = [
    # 1X2 entre eux
    frozenset({"home_win",  "away_win"}),
    frozenset({"home_win",  "draw"}),
    frozenset({"away_win",  "draw"}),
    # Chances doubles entre elles (se chevauchent)
    frozenset({"home_draw", "away_draw"}),   # 1X et X2 partagent le nul
    frozenset({"home_draw", "home_away"}),   # 1X et 12 partagent dom.
    frozenset({"away_draw", "home_away"}),   # X2 et 12 partagent ext.
    # Chances doubles vs 1X2 redondants
    frozenset({"home_win",  "home_draw"}),
    frozenset({"home_win",  "home_away"}),
    frozenset({"away_win",  "away_draw"}),
    frozenset({"away_win",  "home_away"}),
    frozenset({"draw",      "home_draw"}),
    frozenset({"draw",      "away_draw"}),
    # Total buts
    frozenset({"over_25",   "under_25"}),
    frozenset({"over_35",   "under_35"}),
    frozenset({"over_35",   "over_25"}),    # over_35 implique over_25
    frozenset({"over_45",   "over_35"}),    # over_45 implique over_35
    frozenset({"over_45",   "over_25"}),
    frozenset({"under_25",  "under_35"}),   # under_25 implique under_35
    # BTTS vs total buts (corrélés)
    frozenset({"btts_yes",  "over_25"}),
    frozenset({"btts_no",   "under_25"}),
    frozenset({"btts_yes",  "btts_no"}),
]


@router.post("/smart-ticket", response_model=SmartTicketOut)
def generate_smart_ticket(
    request: SmartTicketRequest,
    db: Session = Depends(get_db),
) -> SmartTicketOut:
    """Génère un ticket optimisé.

    Modes :
        simple   — meilleur pari unique par match (safe ≥ 60%)
        combined — plusieurs paris indépendants par match (safe ≥ 60%)
        hot      — paris risqués à haute valeur (proba 35-59%)
    """
    is_hot = request.mode == "hot"
    proba_min = SEUIL_HOT_MIN if is_hot else SEUIL_SAFE_MIN
    proba_max = SEUIL_HOT_MAX if is_hot else 1.0

    candidates: list[SelectionItem] = []
    confidence_scores: list[int] = []
    first_pred_id: Optional[int] = None

    # ── Collecte des candidats ────────────────────────────────────────────────
    for match_id in request.match_ids:
        try:
            pred, _ = prediction_service.get_or_create_prediction(match_id, db)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Match {match_id} : {exc}")

        if first_pred_id is None:
            first_pred_id = pred.id
        if pred.confidence_score is not None:
            confidence_scores.append(pred.confidence_score)

        for bet_type, (attr, label) in _CANDIDATE_TYPES.items():
            raw: Optional[float] = getattr(pred, attr, None)
            if raw is None:
                continue
            proba = (1.0 - raw) if bet_type in _INVERSE_TYPES else raw
            if proba_min <= proba <= proba_max:
                candidates.append(SelectionItem(
                    match_id=match_id,
                    bet_type=bet_type,
                    label=label,
                    probability=proba,
                ))

    # ── Sélection gloutonne anti-corrélation ─────────────────────────────────
    candidates.sort(key=lambda c: c.probability, reverse=True)

    selected: list[SelectionItem] = []
    correlated_warning: Optional[str] = None
    seen_matches_simple: set[int] = set()

    for cand in candidates:
        if len(selected) >= MAX_SELECTIONS:
            break

        # Mode simple : 1 seul pari par match
        if request.mode == "simple" and cand.match_id in seen_matches_simple:
            continue

        # Anti-corrélation intra-match
        is_correlated = False
        for already in selected:
            if already.match_id == cand.match_id:
                pair = frozenset({already.bet_type, cand.bet_type})
                if pair in _CORRELATED_PAIRS:
                    is_correlated = True
                    correlated_warning = (
                        f"Paris corrélés détectés ({already.bet_type} / {cand.bet_type}) "
                        "— sélection ajustée automatiquement."
                    )
                    break

        if not is_correlated:
            selected.append(cand)
            seen_matches_simple.add(cand.match_id)

    if not selected:
        msg = (
            "Aucun pari risqué trouvé dans la plage 35-59% pour ces matchs."
            if is_hot else
            "Aucune sélection disponible avec le seuil actuel (min 60%)."
        )
        raise HTTPException(status_code=422, detail=msg)

    # ── Métriques ─────────────────────────────────────────────────────────────
    combined_proba: float = reduce(lambda acc, s: acc * s.probability, selected, 1.0)
    confidence_score: int = (
        int(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 50
    )

    # ── Persistance ───────────────────────────────────────────────────────────
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
        "Ticket id=%d mode=%s | %d sélections | combined_proba=%.3f",
        ticket_orm.id, request.mode, len(selected), combined_proba,
    )

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
