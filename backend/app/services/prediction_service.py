"""PredictionService: generate and cache predictions using the Poisson ML model.

Phase 3A : pondération temporelle xi + features de forme
Phase 3A+ : sauvegarde/chargement du modèle en .pkl

Stratégie de cache :
  1. Si model.pkl existe et est récent (< MODEL_TTL_HOURS) → on le charge
  2. Sinon → on entraîne depuis la BDD et on sauvegarde
  3. invalidate_model() supprime le .pkl → force ré-entraînement
"""
import logging
import time
import pickle
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.match import Match
from app.models.match_stat import MatchStat
from app.models.prediction import Prediction
from app.services.understat_client import understat_client

# XGBoost (Phase 3E)
_XGB_MODEL = None
_XGB_PKL = Path(__file__).parent.parent.parent.parent / "ml" / "model_cache" / "xgb_model.pkl"


if TYPE_CHECKING:
    from models.poisson_model import PoissonModel

logger = logging.getLogger(__name__)

_ML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ml"
_MODEL_VERSION = "dixon_coles_xgboost_ensemble_v1"

# Chemin de sauvegarde du modèle sérialisé
_MODEL_PKL = Path(__file__).resolve().parent.parent.parent / "model_cache" / "model.pkl"

# Durée de validité du cache pkl : 24h
# Au-delà, on ré-entraîne automatiquement pour intégrer les nouveaux matchs
_MODEL_TTL_HOURS = 24

_model: "PoissonModel | None" = None
_model_lock = threading.Lock()


def _ensure_ml_path() -> None:
    ml_str = str(_ML_PATH)
    if ml_str not in sys.path:
        sys.path.insert(0, ml_str)
        logger.debug("Added ML path: %s", ml_str)


def _pkl_is_fresh() -> bool:
    """Vérifie si le fichier .pkl existe et date de moins de MODEL_TTL_HOURS."""
    if not _MODEL_PKL.exists():
        return False
    age_hours = (datetime.now().timestamp() - _MODEL_PKL.stat().st_mtime) / 3600
    return age_hours < _MODEL_TTL_HOURS


def _load_model_from_pkl() -> "PoissonModel | None":
    """Charge le modèle depuis le .pkl. Retourne None si échec."""
    try:
        _ensure_ml_path()
        with open(_MODEL_PKL, "rb") as f:
            model = pickle.load(f)
        logger.info("Modèle chargé depuis %s", _MODEL_PKL)
        return model
    except Exception as exc:
        logger.warning("Impossible de charger le .pkl : %s", exc)
        return None


def _save_model_to_pkl(model: "PoissonModel") -> None:
    """Sauvegarde le modèle en .pkl. Crée le dossier si nécessaire."""
    try:
        _MODEL_PKL.parent.mkdir(parents=True, exist_ok=True)
        with open(_MODEL_PKL, "wb") as f:
            pickle.dump(model, f)
        logger.info("Modèle sauvegardé → %s", _MODEL_PKL)
    except Exception as exc:
        logger.error("Erreur sauvegarde .pkl : %s", exc)


def _train_model_from_db(db: Session) -> "PoissonModel":
    """Entraîne le modèle sur les matchs FINISHED avec pondération temporelle."""
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
            Match.match_date,
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

    now = datetime.now(timezone.utc)

    def _days_ago(dt: datetime) -> float:
        if dt is None:
            return 365.0
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (now - dt).total_seconds() / 86400)

    df["days_ago"] = df["match_date"].apply(_days_ago)

    model = PoissonModel(max_goals=6, xi=0.0015)
    model.fit(df)
    logger.info("PoissonModel entraîné — %d matchs | xi=%.4f", len(df), model.xi)
    return model


def get_model(db: Session) -> "PoissonModel":
    """Retourne le singleton PoissonModel.

    Ordre de priorité :
      1. Singleton en mémoire (déjà chargé dans ce process)
      2. Cache .pkl frais (< 24h) → chargement instantané
      3. Ré-entraînement depuis la BDD + sauvegarde .pkl
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                if _pkl_is_fresh():
                    loaded = _load_model_from_pkl()
                    if loaded is not None:
                        _model = loaded
                        return _model
                # Entraînement complet
                _model = _train_model_from_db(db)
                _save_model_to_pkl(_model)
    return _model


def invalidate_model() -> None:
    """Supprime le .pkl et le singleton → ré-entraînement au prochain appel."""
    global _model
    with _model_lock:
        _model = None
        if _MODEL_PKL.exists():
            _MODEL_PKL.unlink()
            logger.info("model.pkl supprimé.")
    logger.info("Cache modèle invalidé — ré-entraînement au prochain appel.")


# ---------------------------------------------------------------------------
# Features de forme (Phase 3A)
# ---------------------------------------------------------------------------

def _compute_form_weights(
    home_team_id: int,
    away_team_id: int,
    db: Session,
    competition_code: str | None = None,
    match_date=None,
) -> tuple[float, float]:
    """Multiplicateurs de forme avec 3 sources par priorite.

    1. Understat xG (saison courante, top 5 ligues)
    2. match_stats BDD xG (api-football historique)
    3. Fallback points V=3/N=1/D=0
    """
    from app.models.team import Team

    def _xg_to_form_w(xg_avg: float) -> float:
        return 0.8 + 0.4 * min(xg_avg / 1.5, 1.0)

    def _team_form(team_id: int) -> float:
        team = db.get(Team, team_id)
        team_name = team.name if team else None

        # Source 1 : Understat (saison courante)
        if team_name and competition_code and match_date:
            try:
                xg_list = understat_client.get_recent_xg(
                    competition_code=competition_code,
                    team_db_name=team_name,
                    match_date=match_date,
                    n=5,
                )
                if xg_list:
                    xg_avg = sum(xg_list) / len(xg_list)
                    form_w = _xg_to_form_w(xg_avg)
                    logger.debug("Understat equipe %d (%s) xg_avg=%.2f -> %.3f", team_id, team_name, xg_avg, form_w)
                    return form_w
            except Exception as exc:
                logger.warning("Understat erreur equipe %d : %s", team_id, exc)

        # Source 2 : match_stats BDD (api-football)
        xg_rows = db.execute(
            select(MatchStat.expected_goals)
            .join(Match, MatchStat.match_id == Match.id)
            .where(
                Match.status == "FINISHED",
                MatchStat.expected_goals.is_not(None),
                (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
                (
                    ((Match.home_team_id == team_id) & (MatchStat.side == "HOME")) |
                    ((Match.away_team_id == team_id) & (MatchStat.side == "AWAY"))
                ),
            )
            .order_by(Match.match_date.desc())
            .limit(5)
        ).all()

        if xg_rows:
            xg_values = [r[0] for r in xg_rows if r[0] is not None]
            if xg_values:
                xg_avg = sum(xg_values) / len(xg_values)
                form_w = _xg_to_form_w(xg_avg)
                logger.debug("BDD-xG equipe %d xg_avg=%.2f -> %.3f", team_id, xg_avg, form_w)
                return form_w

        # Source 3 : fallback points
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
            return 1.0

        points = 0
        for home_id, away_id, hs, aws in rows:
            if home_id == team_id:
                if hs > aws:    points += 3
                elif hs == aws: points += 1
            else:
                if aws > hs:    points += 3
                elif aws == hs: points += 1

        form_w = 0.8 + 0.4 * (points / 15.0)
        logger.debug("Points equipe %d pts=%d -> %.3f", team_id, points, form_w)
        return form_w

    fh = _team_form(home_team_id)
    fa = _team_form(away_team_id)
    logger.debug("Forme finale dom=%.3f ext=%.3f", fh, fa)
    return fh, fa


# ---------------------------------------------------------------------------
# XGBoost helpers (Phase 3E)
# ---------------------------------------------------------------------------

def _get_xgb_model():
    """Singleton XGBoost avec cache pkl 24h."""
    global _XGB_MODEL
    if _XGB_MODEL is not None:
        return _XGB_MODEL

    import sys
    ml_path = Path(__file__).parent.parent.parent.parent / "ml"
    if str(ml_path) not in sys.path:
        sys.path.insert(0, str(ml_path))

    from models.xgboost_model import XGBoostModel

    if _XGB_PKL.exists() and (time.time() - _XGB_PKL.stat().st_mtime) < 86400:
        try:
            with open(_XGB_PKL, "rb") as f:
                _XGB_MODEL = pickle.load(f)
            logger.info("XGBoost charge depuis pkl.")
            return _XGB_MODEL
        except Exception:
            pass

    logger.info("Entrainement XGBoost...")
    import pandas as pd
    features_path = ml_path / "data" / "processed" / "features.parquet"
    df = pd.read_parquet(features_path)
    model = XGBoostModel()
    metrics = model.fit(df)
    logger.info("XGBoost entraine : %s", metrics)

    _XGB_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(_XGB_PKL, "wb") as f:
        pickle.dump(model, f)

    _XGB_MODEL = model
    return _XGB_MODEL


def _get_team_features_avg5(team_id: int, match_date, db: Session) -> dict:
    """Calcule les features avg5 depuis la BDD pour le modele XGBoost."""
    rows = db.execute(
        select(Match.home_team_id, Match.away_team_id,
               Match.home_score, Match.away_score)
        .where(
            Match.status == "FINISHED",
            Match.home_score.is_not(None),
            Match.away_score.is_not(None),
            Match.match_date < match_date,
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
        )
        .order_by(Match.match_date.desc())
        .limit(5)
    ).all()

    if not rows:
        return {"goals_scored_avg5": 1.5, "goals_conceded_avg5": 1.5,
                "points_avg5": 1.5, "gd_avg5": 0.0, "win_rate5": 0.4}

    goals_scored, goals_conceded, points, wins = [], [], [], []
    for home_id, away_id, hs, aws in rows:
        is_home = (home_id == team_id)
        scored   = hs  if is_home else aws
        conceded = aws if is_home else hs
        goals_scored.append(scored)
        goals_conceded.append(conceded)
        if scored > conceded:    points.append(3); wins.append(1)
        elif scored == conceded: points.append(1); wins.append(0)
        else:                    points.append(0); wins.append(0)

    n = len(rows)
    return {
        "goals_scored_avg5":   sum(goals_scored)   / n,
        "goals_conceded_avg5": sum(goals_conceded)  / n,
        "points_avg5":         sum(points)          / n,
        "gd_avg5":             (sum(goals_scored) - sum(goals_conceded)) / n,
        "win_rate5":           sum(wins)            / n,
    }


def _blend_probas(dc: dict, xgb_pred: dict, w_dc: float = 0.6, w_xgb: float = 0.4) -> dict:
    """Fusionne les probabilites Dixon-Coles et XGBoost."""
    hw = w_dc * dc["home_win_proba"] + w_xgb * xgb_pred["home_win"]
    dr = w_dc * dc["draw_proba"]     + w_xgb * xgb_pred["draw"]
    aw = w_dc * dc["away_win_proba"] + w_xgb * xgb_pred["away_win"]
    total = hw + dr + aw
    return {
        "home_win_proba": hw / total,
        "draw_proba":     dr / total,
        "away_win_proba": aw / total,
    }

# ---------------------------------------------------------------------------
# Service principal
# ---------------------------------------------------------------------------

class PredictionService:

    def get_or_create_prediction(
        self,
        match_id: int,
        db: Session,
        force_refresh: bool = False,
    ) -> tuple[Prediction, dict]:
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

        comp_code = None
        if match.competition_id:
            comp = db.get(Competition, match.competition_id)
            if comp:
                comp_code = comp.code

        form_weight_home, form_weight_away = _compute_form_weights(
            match.home_team_id, match.away_team_id, db,
            competition_code=comp_code,
            match_date=match.match_date,
        )

        model = get_model(db)
        matrix = model.predict(
            match.home_team_id,
            match.away_team_id,
            form_weight_home=form_weight_home,
            form_weight_away=form_weight_away,
        )

        raw_preds = score_matrix_to_predictions(matrix)
        raw_preds["form_weight_home"] = form_weight_home
        raw_preds["form_weight_away"] = form_weight_away


        # ── Fusion XGBoost (Phase 3E) ────────────────────────────────────
        try:
            xgb_model = _get_xgb_model()
            home_feat = _get_team_features_avg5(match.home_team_id, match.match_date, db)
            away_feat = _get_team_features_avg5(match.away_team_id, match.match_date, db)
            xgb_pred  = xgb_model.predict(home_feat, away_feat)
            blended   = _blend_probas(raw_preds, xgb_pred, w_dc=0.6, w_xgb=0.4)
            raw_preds["home_win_proba"] = blended["home_win_proba"]
            raw_preds["draw_proba"]     = blended["draw_proba"]
            raw_preds["away_win_proba"] = blended["away_win_proba"]
            raw_preds["xgb_home_win"]   = xgb_pred["home_win"]
            raw_preds["xgb_draw"]       = xgb_pred["draw"]
            raw_preds["xgb_away_win"]   = xgb_pred["away_win"]
            logger.info("XGBoost fusion OK : xgb=(%.2f/%.2f/%.2f) blend=(%.2f/%.2f/%.2f)",
                xgb_pred["home_win"], xgb_pred["draw"], xgb_pred["away_win"],
                blended["home_win_proba"], blended["draw_proba"], blended["away_win_proba"])
        except Exception as exc:
            logger.warning("XGBoost indisponible, DC seul : %s", exc)
        # ─────────────────────────────────────────────────────────────────
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
        n_teams = len(getattr(model, "teams", []))
        data_quality = min(1.0, n_teams / 40)

        hw = preds.get("home_win_proba") or 0.33
        d  = preds.get("draw_proba")     or 0.33
        aw = preds.get("away_win_proba") or 0.33
        model_stability = max(0.0, 1.0 - abs(hw + d + aw - 1.0))

        max_p = max(hw, d, aw)
        prediction_coherence = min(1.0, max(0.0, (max_p - 0.33) * 3.0))

        fh = preds.get("form_weight_home", 1.0)
        fa = preds.get("form_weight_away", 1.0)
        form_asymmetry = min(1.0, abs(fh - fa) / 0.4)

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
