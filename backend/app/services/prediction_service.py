"""PredictionService — orchestre le modèle Poisson et la persistance BDD.

Le modèle PoissonModel est instancié une seule fois (singleton thread-safe)
et ré-entraîné à chaque redémarrage du serveur depuis les matchs FINISHED en BDD.
"""

import logging
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction

if TYPE_CHECKING:
    from models.poisson_model import PoissonModel

logger = logging.getLogger(__name__)

_MODEL_VERSION = "poisson_dixon_coles_v1"

# Chemin vers ml/ — ajouté au sys.path lors du premier import ML
_ML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ml"


def _ensure_ml_path() -> None:
    """Ajoute ml/ au sys.path si nécessaire (lazy, une seule fois)."""
    ml_str = str(_ML_PATH)
    if ml_str not in sys.path:
        sys.path.insert(0, ml_str)


# ---------------------------------------------------------------------------
# Singleton du modèle ML (thread-safe, lazy init)
# ---------------------------------------------------------------------------

_model: "PoissonModel | None" = None
_model_lock = threading.Lock()


def _train_model_from_db(db: Session) -> "PoissonModel":
    """Entraîne un PoissonModel sur tous les matchs FINISHED en BDD.

    Args:
        db: Session SQLAlchemy active.

    Returns:
        PoissonModel entraîné.

    Raises:
        HTTPException 503: Si pas assez de données pour entraîner.
    """
    rows = (
        db.query(
            Match.id,
            Match.home_team_id,
            Match.away_team_id,
            Match.home_score,
            Match.away_score,
        )
        .filter(
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        )
        .all()
    )

    if len(rows) < 10:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Pas assez de matchs terminés pour entraîner le modèle "
                f"({len(rows)} trouvés, 10 minimum requis). "
                "Lancez d'abord le pipeline d'ingestion."
            ),
        )

    _ensure_ml_path()
    from models.poisson_model import PoissonModel  # noqa: PLC0415

    df = pd.DataFrame(rows, columns=["id", "home_team_id", "away_team_id", "home_score", "away_score"])
    model = PoissonModel(max_goals=5)
    model.fit(df)
    logger.info("Modèle Poisson entraîné sur %d matchs.", len(df))
    return model


def get_model(db: Session) -> "PoissonModel":
    """Retourne le modèle ML singleton, en l'entraînant si nécessaire.

    Utilise le double-checked locking pour la thread-safety.

    Args:
        db: Session SQLAlchemy (utilisée uniquement si le modèle doit être entraîné).

    Returns:
        Instance PoissonModel entraînée.
    """
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            _model = _train_model_from_db(db)
    return _model


def invalidate_model() -> None:
    """Force le ré-entraînement du modèle lors de la prochaine requête.

    À appeler après une ingestion de nouvelles données.
    """
    global _model
    with _model_lock:
        _model = None
    logger.info("Cache modèle invalidé — ré-entraînement au prochain appel.")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class PredictionService:
    """Orchestre la génération et la persistance des prédictions.

    Usage:
        service = PredictionService()
        prediction = service.get_or_create_prediction(match_id=42, db=db)
    """

    def get_or_create_prediction(
        self, match_id: int, db: Session
    ) -> tuple[Prediction, dict]:
        """Retourne la prédiction existante ou en génère une nouvelle.

        Si une prédiction existe déjà pour ce match, elle est retournée telle quelle.
        Sinon, le modèle Poisson est utilisé pour calculer toutes les probabilités,
        qui sont sauvegardées en BDD avant d'être retournées.

        Args:
            match_id: ID interne du match.
            db: Session SQLAlchemy active.

        Returns:
            Tuple (Prediction ORM, dict enrichi avec top_scores et autres champs
            non stockés en BDD).

        Raises:
            HTTPException 404: Si le match n'existe pas.
            HTTPException 422: Si le match n'a pas d'équipes renseignées.
            HTTPException 503: Si pas assez de données pour entraîner le modèle.
        """
        # 1. Prédiction déjà en BDD ?
        existing = (
            db.query(Prediction).filter(Prediction.match_id == match_id).first()
        )
        if existing:
            logger.debug("Prédiction en cache BDD pour match_id=%d", match_id)
            return existing, {}

        # 2. Vérifier que le match existe
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail=f"Match {match_id} introuvable.")
        if not match.home_team_id or not match.away_team_id:
            raise HTTPException(
                status_code=422,
                detail=f"Match {match_id} sans équipes renseignées.",
            )

        # 3. Charger / entraîner le modèle
        model = get_model(db)

        # 4. Calcul de la matrice de scores
        _ensure_ml_path()
        from engine.score_matrix import predictions_to_db_row, score_matrix_to_predictions  # noqa: PLC0415

        matrix = model.predict(match.home_team_id, match.away_team_id)
        full_preds = score_matrix_to_predictions(matrix)

        # 5. Confidence score (formule de la spec prediction-engine)
        confidence = self._compute_confidence(full_preds, model)

        # 6. Champs DB-compatibles
        db_row = predictions_to_db_row(full_preds)
        db_row["confidence_score"] = confidence

        # 7. Persistance
        prediction = Prediction(
            match_id=match_id,
            model_version=_MODEL_VERSION,
            **db_row,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        logger.info("Prédiction générée et sauvegardée pour match_id=%d", match_id)

        # extra = champs enrichis non stockés en BDD
        extra = {"top_scores": full_preds.get("top_scores", [])}
        return prediction, extra

    @staticmethod
    def _compute_confidence(preds: dict, model: "PoissonModel") -> int:
        """Calcule le score de confiance (0-100) selon la spec prediction-engine.

        Args:
            preds: Dict complet de predictions (sortie de score_matrix_to_predictions).
            model: Modèle Poisson entraîné (pour estimer la qualité des données).

        Returns:
            Entier entre 0 et 100.
        """
        # data_quality : proxy = nombre d'équipes connues / total équipes
        data_quality = min(len(model.teams) / 20, 1.0)

        # model_stability : fixé à 0.7 pour Poisson (modèle stable mais simplifié)
        model_stability = 0.70

        # prediction_coherence : la proba max parmi H/D/A (plus elle est haute, plus c'est clair)
        max_result = max(
            preds.get("home_win_proba", 0.33),
            preds.get("draw_proba", 0.33),
            preds.get("away_win_proba", 0.33),
        )
        prediction_coherence = min(max_result / 0.7, 1.0)

        # match_volatility : inverse de la certitude (1 = match très incertain)
        match_volatility = 1.0 - max_result

        score = (
            data_quality * 0.3
            + model_stability * 0.3
            + prediction_coherence * 0.2
            + (1.0 - match_volatility) * 0.2
        ) * 100
        return int(score)


# Module-level singleton
prediction_service = PredictionService()
