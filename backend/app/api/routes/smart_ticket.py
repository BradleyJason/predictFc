"""Routes FastAPI — Smart Ticket.

POST /smart-ticket — génère un combiné optimal depuis une liste de matchs

Règles (spec prediction-engine) :
  - Seuil minimum : 60% par sélection
  - Maximum 3 sélections
  - Détection et exclusion des paris corrélés
  - Score de confiance global (0-100)
  - Disclaimer légal obligatoire
"""

import logging
from functools import reduce

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.smart_ticket import SmartTicket
from app.schemas.smart_ticket import SelectionItem, SmartTicketOut, SmartTicketRequest
from app.services.prediction_service import prediction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smart-ticket", tags=["smart-ticket"])

# ---------------------------------------------------------------------------
# Constantes (spec prediction-engine)
# ---------------------------------------------------------------------------

_SEUIL_MIN_PROBA = 0.60
_MAX_SELECTIONS = 3

# Types de paris candidats : (clé_type, label_affichage, attribut_Prediction)
_CANDIDATE_TYPES: list[tuple[str, str, str]] = [
    ("home_win",  "Victoire Domicile",          "home_win_proba"),
    ("away_win",  "Victoire Extérieur",          "away_win_proba"),
    ("draw",      "Match Nul",                   "draw_proba"),
    ("btts_yes",  "Les deux équipes marquent",   "btts_proba"),
    ("over_25",   "Plus de 2.5 buts",            "over_25_proba"),
    ("over_15",   "Plus de 1.5 buts",            "over_15_proba"),
    ("home_draw", "Chance double 1X",            "home_draw_proba"),
    ("away_draw", "Chance double X2",            "away_draw_proba"),
]

# Paires corrélées : ne pas combiner au sein d'un même match
# Basé sur la spec prediction-engine (corrélation > 70%)
_CORRELATED_PAIRS: set[frozenset] = {
    frozenset({"over_25",   "btts_yes"}),   # ~75% de corrélation
    frozenset({"home_win",  "home_draw"}),  # home_draw = 1X inclut home_win
    frozenset({"away_win",  "away_draw"}),  # away_draw = X2 inclut away_win
    frozenset({"draw",      "home_draw"}),  # home_draw = 1X inclut draw
    frozenset({"draw",      "away_draw"}),  # away_draw = X2 inclut draw
}


def _are_correlated(type_a: str, type_b: str) -> bool:
    """Vérifie si deux types de paris sont corrélés (pour le même match)."""
    return frozenset({type_a, type_b}) in _CORRELATED_PAIRS


def _compute_confidence(selections: list[SelectionItem]) -> int:
    """Calcule le score de confiance global du ticket.

    Formule spec prediction-engine :
      score = (data_quality×0.3 + model_stability×0.3
               + prediction_coherence×0.2 + (1-match_volatility)×0.2) × 100

    Args:
        selections: Sélections retenues dans le ticket.

    Returns:
        Score entier entre 0 et 100.
    """
    if not selections:
        return 0

    avg_proba = sum(s.probability for s in selections) / len(selections)
    max_proba = max(s.probability for s in selections)

    data_quality = 0.80          # proxy : modèle entraîné = bonne qualité
    model_stability = 0.70       # Poisson : stable mais simplifié
    prediction_coherence = min(avg_proba / 0.80, 1.0)
    match_volatility = 1.0 - max_proba

    score = (
        data_quality * 0.3
        + model_stability * 0.3
        + prediction_coherence * 0.2
        + (1.0 - match_volatility) * 0.2
    ) * 100
    return int(score)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("", response_model=SmartTicketOut, status_code=201)
def generate_smart_ticket(
    body: SmartTicketRequest,
    db: Session = Depends(get_db),
) -> SmartTicketOut:
    """Génère un Smart Ticket optimisé pour une liste de matchs.

    Algorithme :
    1. Récupère (ou génère) les prédictions pour chaque match.
    2. Construit la liste des paris candidats (probabilité ≥ 60%).
    3. Écarte les paris corrélés (sur le même match).
    4. Trie par probabilité décroissante, sélectionne au max 3.
    5. En mode "simple" : une seule sélection par match.
       En mode "combined" : jusqu'à 3 sélections multi-matchs.
    6. Calcule la probabilité combinée et le score de confiance.
    7. Sauvegarde en BDD et retourne avec disclaimer légal.

    Args:
        body: Liste d'IDs de matchs + mode (simple|combined).
        db: Session BDD injectée.

    Returns:
        SmartTicketOut avec sélections, combined_proba, confidence_score, disclaimer.
    """
    # 1. Récupération des prédictions
    predictions_with_extra: list = []
    for mid in body.match_ids:
        pred, extra = prediction_service.get_or_create_prediction(mid, db)
        predictions_with_extra.append((pred, extra))

    # 2. Construction des candidats
    candidates: list[SelectionItem] = []
    for pred, _ in predictions_with_extra:
        for bet_type, label, attr in _CANDIDATE_TYPES:
            proba = getattr(pred, attr, None)
            if proba is not None and proba >= _SEUIL_MIN_PROBA:
                candidates.append(
                    SelectionItem(
                        match_id=pred.match_id,
                        prediction_id=pred.id,
                        type=bet_type,
                        label=label,
                        probability=proba,
                    )
                )

    # 3. Tri par probabilité décroissante
    candidates.sort(key=lambda c: c.probability, reverse=True)

    # 4. Sélection greedy (no-correlation, max 3, mode simple/combined)
    selected: list[SelectionItem] = []
    correlated_warning = False
    seen_matches: set[int] = set()

    for candidate in candidates:
        if len(selected) >= _MAX_SELECTIONS:
            break

        # Mode "simple" : une seule sélection par match
        if body.mode == "simple" and candidate.match_id in seen_matches:
            continue

        # Vérification corrélation (uniquement intra-match)
        is_corr = any(
            candidate.match_id == s.match_id
            and _are_correlated(candidate.type, s.type)
            for s in selected
        )
        if is_corr:
            correlated_warning = True
            continue

        selected.append(candidate)
        seen_matches.add(candidate.match_id)

    # 5. Probabilité combinée (produit des probas)
    combined_proba: float | None = None
    if selected:
        combined_proba = reduce(lambda a, b: a * b.probability, selected, 1.0)

    # 6. Score de confiance
    confidence = _compute_confidence(selected) if selected else 0

    # 7. Persistance en BDD
    # On rattache le ticket au premier match de la liste pour la FK
    first_pred_id = predictions_with_extra[0][0].id if predictions_with_extra else None
    first_match_id = body.match_ids[0]

    ticket_orm = SmartTicket(
        match_id=first_match_id,
        prediction_id=first_pred_id,
        selections=[s.model_dump() for s in selected],
        combined_proba=combined_proba,
        confidence_score=confidence,
        mode=body.mode,
    )
    db.add(ticket_orm)
    db.commit()
    db.refresh(ticket_orm)

    logger.info(
        "Smart Ticket créé id=%d | %d sélections | combined_proba=%.3f",
        ticket_orm.id,
        len(selected),
        combined_proba or 0,
    )

    return SmartTicketOut(
        id=ticket_orm.id,
        match_id=ticket_orm.match_id,
        prediction_id=ticket_orm.prediction_id,
        mode=body.mode,
        selections=selected,
        combined_proba=combined_proba,
        confidence_score=confidence,
        correlated_warning=correlated_warning,
    )
