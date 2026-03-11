"""Routes for match predictions."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.prediction import DISCLAIMER, PredictionOut, TopScore
from app.services.prediction_service import invalidate_model, prediction_service

router = APIRouter(tags=["predictions"])


@router.get("/predictions/{match_id}", response_model=PredictionOut)
def get_prediction(
    match_id: int,
    force_refresh: bool = Query(False, description="Force la régénération même si déjà en BDD"),
    db: Session = Depends(get_db),
) -> PredictionOut:
    """Return a prediction for the given match, computing it if necessary.

    Args:
        match_id:      Match PK.
        force_refresh: If true, ignore the cached DB row and recompute.

    Raises:
        422: If the match doesn't exist or the model can't produce a prediction.
        500: Unexpected runtime error.
    """
    try:
        pred, raw_preds = prediction_service.get_or_create_prediction(
            match_id, db, force_refresh=force_refresh
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la prédiction : {exc}"
        )

    # Build top_scores from the raw ML output (not stored in DB)
    top_scores: list[TopScore] = [
        TopScore(
            home=s["home"],
            away=s["away"],
            probability=s["proba"],
        )
        for s in raw_preds.get("top_scores", [])
    ]

    return PredictionOut(
        id=pred.id,
        match_id=pred.match_id,
        model_version=pred.model_version,
        home_win_proba=pred.home_win_proba,
        draw_proba=pred.draw_proba,
        away_win_proba=pred.away_win_proba,
        # Prefer float from raw ML output; fall back to stored value
        predicted_home_score=(
            raw_preds.get("predicted_home_score") or pred.predicted_home_score
        ),
        predicted_away_score=(
            raw_preds.get("predicted_away_score") or pred.predicted_away_score
        ),
        exact_score_proba=pred.exact_score_proba,
        over_05_proba=pred.over_05_proba,
        over_15_proba=pred.over_15_proba,
        over_25_proba=pred.over_25_proba,
        over_35_proba=pred.over_35_proba,
        over_45_proba=pred.over_45_proba,
        btts_proba=pred.btts_proba,
        home_draw_proba=pred.home_draw_proba,
        away_draw_proba=pred.away_draw_proba,
        home_away_proba=pred.home_away_proba,
        home_qualify_proba=pred.home_qualify_proba,
        away_qualify_proba=pred.away_qualify_proba,
        confidence_score=pred.confidence_score,
        top_scores=top_scores,
        disclaimer=DISCLAIMER,
    )


@router.post("/predictions/invalidate-model", tags=["predictions"])
def invalidate_model() -> dict:
    """Reset the in-memory PoissonModel singleton.

    The next prediction request will retrain the model from DB data.
    Useful after ingesting new match results.
    """
    return {"message": "Modèle réinitialisé. Il sera réentraîné automatiquement à la prochaine prédiction."}
