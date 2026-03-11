"""PredictionService: generate and cache predictions using the Poisson ML model.

Phase 3A — Nouvelles features :
- days_ago : pondération temporelle dans le fit()
- form_weight_home/away : multiplicateurs de forme sur les lambdas de predict()
  calculés à partir des 5 derniers matchs de chaque équipe (V=3, N=1, D=0)

Design :
- Imports ML lazy (FastAPI démarre même sans ml/)
- Singleton PoissonModel protégé par threading.Lock (double-checked locking)
"""
import logging
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction
from app.schemas.prediction import TopScore

if TYPE_CHECKING:
    from models.poisson_model import PoissonModel

logger = logging.getLogger(__name__)

_ML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ml"
_MODEL_VERSION = "poisson_dixon_coles_v2_temporal"

_model: "PoissonModel | None" = None
_model_lock = threading.Lock()


def _ensure_ml_path() -> None:
    ml_str = str(_ML_PATH)
    if ml_str not in sys.path:
        sys.path.insert(0, ml_str)
        logger.debug("Added ML path: %s", ml_str)


def _train_model_from_db(db: Session) -> "PoissonModel":
    """Entraîne le modèle sur les matchs FINISHED avec pondération temporelle.

    Nouveauté Phase 3A : on récupère match_date pour calculer days_ago,
    ce qui active la pondération temporelle xi dans PoissonModel.fit().
    """
    _ensure_ml_path()
    import pandas as pd
    from models.poisson_model import PoissonModel

    rows = db.execute(
        select(
            Match.id,
            Match.home_team_id,
            Match.away_team_id,
            Match.home_score,
            Match.away_score,
            Match.match_date,          # ← nouveau : pour pondération temporelle
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
        columns=["match_id", "home_team_id", "away_team_id",
                 "home_score", "away_score", "match_date"],
    )

    # ── Calcul de days_ago ──────────────────────────────────────────────────
    # days_ago = nombre de jours entre le match et aujourd'hui
    # Plus days_ago est grand → poids exp(-xi * days_ago) est petit
    now = datetime.now(timezone.utc)

    def _days_ago(dt: datetime) -> float:
        if dt is None:
            return 365.0  # valeur par défaut : 1 an
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (now - dt).total_seconds() / 86400)

    df["days_ago"] = df["match_date"].apply(_days_ago)

    model = PoissonModel(max_goals=6, xi=0.0015)
    model.fit(df)
    logger.info(
        "PoissonModel v2 entraîné — %d matchs | xi=%.4f",
        len(df), model.xi,
    )
    return model


def get_model(db: Session) -> "PoissonModel":
    """Retourne le singleton PoissonModel, en l'entraînant si nécessaire."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = _train_model_from_db(db)
    return _model


def invalidate_model() -> None:
    """Force le ré-entraînement au prochain appel."""
    global _model
    with _model_lock:
        _model = None
    logger.info("Cache modèle invalidé.")


# ---------------------------------------------------------------------------
# Calcul des features de forme
# ---------------------------------------------------------------------------

def _compute_form_weights(
    home_team_id: int,
    away_team_id: int,
    db: Session,
) -> tuple[float, float]:
    """Calcule les multiplicateurs de forme pour les deux équipes.

    Pour chaque équipe, on récupère les 5 derniers matchs FINISHED
    et on calcule un score de forme normalisé autour de 1.0 :

        points  = Σ (V=3, N=1, D=0) sur 5 matchs      → max = 15
        form_w  = 0.8 + 0.4 * (points / 15)
                → plage [0.8 ; 1.2]

    Exemples :
        5 victoires  → 15 pts → form_w = 1.2   (+20% sur les lambdas)
        3V 1N 1D     → 10 pts → form_w = 1.07
        Forme neutre → 7.5 pts → form_w = 1.0  (valeur centrale)
        5 défaites   → 0 pts  → form_w = 0.8   (-20% sur les lambdas)

    Args:
        home_team_id: ID de l'équipe à domicile.
        away_team_id: ID de l'équipe à l'extérieur.
        db:           Session SQLAlchemy.

    Returns:
        (form_weight_home, form_weight_away) — deux floats dans [0.8, 1.2].
    """
    def _team_form(team_id: int) -> float:
        # Récupère les 5 derniers matchs FINISHED de cette équipe
        rows = db.execute(
            select(Match.home_team_id, Match.away_team_id,
                   Match.home_score, Match.away_score)
            .where(
                Match.status == "FINISHED",
                Match.home_score.is_not(None),
                Match.away_score.is_not(None),
                (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            )
            .order_by(Match.match_date.desc())
            .limit(5)
        ).all()

        if not rows:
            return 1.0  # équipe inconnue → forme neutre

        points = 0
        for home_id, away_id, hs, aws in rows:
            if home_id == team_id:
                # L'équipe jouait à domicile
                if hs > aws:
                    points += 3   # victoire
                elif hs == aws:
                    points += 1   # nul
                # défaite → 0
            else:
                # L'équipe jouait à l'extérieur
                if aws > hs:
                    points += 3
                elif aws == hs:
                    points += 1

        # Normalisation : max 15 pts → form_w ∈ [0.8, 1.2]
        return 0.8 + 0.4 * (points / 15.0)

    form_home = _team_form(home_team_id)
    form_away = _team_form(away_team_id)

    logger.debug(
        "Forme — domicile=%.3f extérieur=%.3f",
        form_home, form_away,
    )
    return form_home, form_away


# ---------------------------------------------------------------------------
# Service principal
# ---------------------------------------------------------------------------

class PredictionService:
    """Génère, persiste et met en cache les prédictions."""

    def get_or_create_prediction(
        self,
        match_id: int,
        db: Session,
        force_refresh: bool = False,
    ) -> tuple[Prediction, dict]:
        """Retourne (Prediction ORM, raw_predictions dict).

        Si force_refresh=False et qu'une ligne existe en BDD, la retourne
        directement sans relancer le modèle.

        Args:
            match_id:      PK du Match.
            db:            Session SQLAlchemy.
            force_refresh: Ignorer le cache BDD et recalculer.

        Returns:
            (Prediction ORM, dict avec les prédictions brutes ML).

        Raises:
            ValueError: Match introuvable ou équipes manquantes.
        """
        if not force_refresh:
            existing = db.scalars(
                select(Prediction).where(Prediction.match_id == match_id)
            ).first()
            if existing:
                return existing, self._prediction_to_dict(existing)

        match = db.get(Match, match_id)
        if not match:
            raise ValueError(f"Match {match_id} introuvable.")
        if match.home_team_id is None or match.away_team_id is None:
            raise ValueError(f"Match {match_id} : équipes manquantes.")

        _ensure_ml_path()
        from engine.score_matrix import predictions_to_db_row, score_matrix_to_predictions

        # ── Phase 3A : calcul des features de forme ─────────────────────────
        form_weight_home, form_weight_away = _compute_form_weights(
            match.home_team_id, match.away_team_id, db
        )

        model = get_model(db)

        # predict() accepte maintenant les multiplicateurs de forme
        matrix = model.predict(
            match.home_team_id,
            match.away_team_id,
            form_weight_home=form_weight_home,
            form_weight_away=form_weight_away,
        )

        raw_preds = score_matrix_to_predictions(matrix)

        # Enrichissement du dict brut avec les infos de forme (pour debug/logs)
        raw_preds["form_weight_home"] = form_weight_home
        raw_preds["form_weight_away"] = form_weight_away

        db_row_data = predictions_to_db_row(raw_preds)
        confidence = self._compute_confidence(raw_preds, model)

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

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _prediction_to_dict(pred: Prediction) -> dict:
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
            "top_scores":           [],
        }

    @staticmethod
    def _compute_confidence(preds: dict, model: "PoissonModel") -> int:
        """Score de confiance 0–100.

        Phase 3A : on intègre la forme dans le score de confiance.
        Une forte asymétrie de forme (une équipe très en forme, l'autre pas)
        augmente la cohérence de la prédiction.
        """
        n_teams = len(getattr(model, "teams", []))
        data_quality = min(1.0, n_teams / 40)

        hw = preds.get("home_win_proba") or 0.33
        d  = preds.get("draw_proba")     or 0.33
        aw = preds.get("away_win_proba") or 0.33
        model_stability = max(0.0, 1.0 - abs(hw + d + aw - 1.0))

        max_p = max(hw, d, aw)
        prediction_coherence = min(1.0, max(0.0, (max_p - 0.33) * 3.0))

        # Bonus forme : asymétrie entre les deux équipes
        fh = preds.get("form_weight_home", 1.0)
        fa = preds.get("form_weight_away", 1.0)
        form_asymmetry = min(1.0, abs(fh - fa) / 0.4)  # 0.4 = écart max possible

        volatility = 0.25 if d > 0.30 else 0.10

        raw = (
            data_quality           * 0.25
            + model_stability      * 0.25
            + prediction_coherence * 0.25
            + form_asymmetry       * 0.05
            + (1.0 - volatility)   * 0.20
        ) * 100

        return max(0, min(100, int(raw)))


prediction_service = PredictionService()
