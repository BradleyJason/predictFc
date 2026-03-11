"""Routes FastAPI — prédictions.

GET /predictions/{match_id} — génère ou récupère les prédictions d'un match
DELETE /predictions/{match_id} — invalide le cache pour régénérer
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.prediction import PredictionOut, TopScore
from app.services.prediction_service import invalidate_model, prediction_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{match_id}", response_model=PredictionOut)
def get_prediction(
    match_id: int,
    force_refresh: bool = Query(False, description="Force la régénération même si déjà en BDD"),
    db: Session = Depends(get_db),
) -> PredictionOut:
    """Retourne les prédictions pour un match, en les générant si nécessaire.

    Le service vérifie d'abord si une prédiction existe en BDD. Si oui, elle est
    retournée directement (cache). Sinon, le modèle Poisson est utilisé pour calculer
    toutes les probabilités (1X2, score exact, over/under, BTTS, chance double).

    Args:
        match_id: ID interne du match.
        force_refresh: Si True, supprime la prédiction existante et régénère.
        db: Session BDD injectée.

    Returns:
        PredictionOut avec toutes les probabilités et le disclaimer légal.

    Raises:
        HTTPException 404: Match introuvable.
        HTTPException 422: Match sans équipes renseignées.
        HTTPException 503: Pas assez de données d'entraînement.
    """
    if force_refresh:
        from app.models.prediction import Prediction

        db.query(Prediction).filter(Prediction.match_id == match_id).delete()
        db.commit()

    prediction, extra = prediction_service.get_or_create_prediction(match_id, db)

    # Conversion en schema de réponse
    out = PredictionOut.model_validate(prediction)

    # Enrichissement avec les champs non stockés en BDD
    top_raw = extra.get("top_scores", [])
    out.top_scores = [TopScore(home=s["home"], away=s["away"], proba=s["proba"]) for s in top_raw]

    return out


@router.post("/invalidate-model", status_code=204)
def invalidate_prediction_model() -> None:
    """Force le ré-entraînement du modèle ML lors de la prochaine requête.

    À appeler après une ingestion de nouvelles données (pipeline ingest).
    """
    invalidate_model()
