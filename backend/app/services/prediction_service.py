"""PredictionService: generate and cache predictions using the Poisson ML model.

Key design decisions:
- ML imports are deferred (lazy) so FastAPI starts even when ml/ files are absent.
- The trained PoissonModel is held as a module-level singleton, protected by a
  threading.Lock with double-checked locking so only one training runs concurrently.
- sys.path is patched at call-time to include the ml/ directory.
"""
import logging
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction
from app.schemas.prediction import TopScore

if TYPE_CHECKING:
    # Only imported at type-check time; avoids ImportError at startup.
    from models.poisson_model import PoissonModel

logger = logging.getLogger(__name__)

# ml/ directory is 4 levels above this file:
# backend/app/services/prediction_service.py
#   → backend/app/services/ → backend/app/ → backend/ → project root
_ML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ml"
_MODEL_VERSION = "poisson_dixon_coles_v1"

# Singleton state
_model: "PoissonModel | None" = None
_model_lock = threading.Lock()


def _ensure_ml_path() -> None:
    """Prepend ml/ to sys.path so `from models.xxx` and `from engine.xxx` work."""
    ml_str = str(_ML_PATH)
    if ml_str not in sys.path:
        sys.path.insert(0, ml_str)
        logger.debug("Added ML path to sys.path: %s", ml_str)


def _train_model_from_db(db: Session) -> "PoissonModel":
    """Query FINISHED matches and fit a new PoissonModel.

    Raises:
        ValueError: If there are no finished matches in the database.
        ImportError: If ml/ modules are not found on sys.path.
    """
    _ensure_ml_path()
    import pandas as pd
    from models.poisson_model import PoissonModel  # lazy import

    rows = db.execute(
        select(
            Match.id,
            Match.home_team_id,
            Match.away_team_id,
            Match.home_score,
            Match.away_score,
        ).where(
            Match.status == "FINISHED",
            Match.home_score.is_not(None),
            Match.away_score.is_not(None),
        )
    ).all()

    if not rows:
        raise ValueError(
            "Aucun match FINISHED en base. Exécutez d'abord le pipeline d'ingestion."
        )

    df = pd.DataFrame(
        rows,
        columns=["match_id", "home_team_id", "away_team_id", "home_score", "away_score"],
    )

    model = PoissonModel(max_goals=6)
    model.fit(df)
    logger.info("PoissonModel entraîné sur %d matchs terminés.", len(df))
    return model


def get_model(db: Session) -> "PoissonModel":
    """Return (or create) the module-level PoissonModel singleton.

    Uses double-checked locking so only one thread trains the model.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = _train_model_from_db(db)
    return _model


def invalidate_model() -> None:
    """Force le ré-entraînement du modèle lors de la prochaine requête."""
    global _model
    with _model_lock:
        _model = None
    logger.info("Cache modèle invalidé — ré-entraînement au prochain appel.")


class PredictionService:
    """High-level service that generates, persists, and caches predictions."""

    def get_or_create_prediction(
        self,
        match_id: int,
        db: Session,
        force_refresh: bool = False,
    ) -> tuple[Prediction, dict]:
        """Return (Prediction ORM row, raw_predictions dict).

        If force_refresh=False and a row already exists in DB, return the cached
        row without running the model again.

        Args:
            match_id:      PK of the Match row.
            db:            SQLAlchemy session.
            force_refresh: Ignore cached DB row and recompute.

        Returns:
            (Prediction ORM instance, dict with raw ML predictions including top_scores).

        Raises:
            ValueError: If match not found or teams are missing.
        """
        # Return cached row if available
        if not force_refresh:
            existing = db.scalars(
                select(Prediction).where(Prediction.match_id == match_id)
            ).first()
            if existing:
                return existing, self._prediction_to_dict(existing)

        # Fetch match
        match = db.get(Match, match_id)
        if not match:
            raise ValueError(f"Match {match_id} introuvable.")
        if match.home_team_id is None or match.away_team_id is None:
            raise ValueError(f"Match {match_id} : équipes manquantes.")

        # Run ML prediction
        _ensure_ml_path()
        from engine.score_matrix import predictions_to_db_row, score_matrix_to_predictions  # noqa: PLC0415

        model = get_model(db)
        matrix = model.predict(match.home_team_id, match.away_team_id)
        raw_preds = score_matrix_to_predictions(matrix)
        db_row_data = predictions_to_db_row(raw_preds)
        confidence = self._compute_confidence(raw_preds, model)

        # Delete old prediction if refreshing
        if force_refresh:
            old = db.scalars(
                select(Prediction).where(Prediction.match_id == match_id)
            ).first()
            if old:
                db.delete(old)
                db.flush()

        pred = Prediction(
            match_id=match_id,
            model_version=_MODEL_VERSION,
            confidence_score=confidence,
            **db_row_data,
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)

        return pred, raw_preds

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _prediction_to_dict(pred: Prediction) -> dict:
        """Convert a cached Prediction ORM row to a raw dict for the API."""
        return {
            "home_win_proba":       pred.home_win_proba,
            "draw_proba":           pred.draw_proba,
            "away_win_proba":       pred.away_win_proba,
            "predicted_home_score": pred.predicted_home_score,
            "predicted_away_score": pred.predicted_away_score,
            "over_05_proba":        pred.over_05_proba,
            "over_15_proba":        pred.over_15_proba,
            "over_25_proba":        pred.over_25_proba,
            "over_35_proba":        pred.over_35_proba,
            "over_45_proba":        pred.over_45_proba,
            "btts_proba":           pred.btts_proba,
            "home_draw_proba":      pred.home_draw_proba,
            "away_draw_proba":      pred.away_draw_proba,
            "home_away_proba":      pred.home_away_proba,
            "confidence_score":     pred.confidence_score,
            "top_scores":           [],  # not persisted; recomputed on refresh
        }

    @staticmethod
    def _compute_confidence(preds: dict, model: "PoissonModel") -> int:
        """Compute a 0–100 confidence score.

        Formula (from prediction-engine skill):
            score = data_quality*0.3 + model_stability*0.3
                  + prediction_coherence*0.2 + (1-volatility)*0.2

        All components are clipped to [0, 1].
        """
        # data_quality: how many teams the model has seen (proxy for coverage)
        n_teams = len(getattr(model, "teams", []))
        data_quality = min(1.0, n_teams / 40)

        # model_stability: probabilities should sum to ~1
        hw = preds.get("home_win_proba") or 0.33
        d  = preds.get("draw_proba")     or 0.33
        aw = preds.get("away_win_proba") or 0.33
        model_stability = max(0.0, 1.0 - abs(hw + d + aw - 1.0))

        # prediction_coherence: how "decisive" the prediction is
        max_p = max(hw, d, aw)
        prediction_coherence = min(1.0, max(0.0, (max_p - 0.33) * 3.0))

        # volatility: high draw probability → more uncertain
        volatility = 0.25 if d > 0.30 else 0.10

        raw = (
            data_quality        * 0.3
            + model_stability   * 0.3
            + prediction_coherence * 0.2
            + (1.0 - volatility) * 0.2
        ) * 100

        return max(0, min(100, int(raw)))


# Module-level singleton
prediction_service = PredictionService()
