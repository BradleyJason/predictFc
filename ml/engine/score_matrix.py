"""Agrégateur — convertit une matrice de scores en toutes les prédictions.

Point d'entrée unique du moteur de prédiction :

    matrix = poisson_model.predict(home_id, away_id)
    predictions = score_matrix_to_predictions(matrix)

Toutes les probabilités se déduisent mathématiquement de P(i,j).
"""

import numpy as np

from ml.engine.predictions.btts import predict_btts
from ml.engine.predictions.double_chance import predict_double_chance
from ml.engine.predictions.exact_score import predict_exact_score
from ml.engine.predictions.goal_gap import predict_goal_gap
from ml.engine.predictions.result import predict_result
from ml.engine.predictions.total_goals import predict_total_goals


def score_matrix_to_predictions(matrix: np.ndarray) -> dict:
    """Convertit une matrice de scores en dictionnaire complet de prédictions.

    La matrice doit être une distribution de probabilité sur les scores :
    matrix[i, j] = P(home_score = i, away_score = j), avec Σ matrix ≈ 1.

    Args:
        matrix: Matrice numpy (n, n) issue de PoissonModel.predict().

    Returns:
        Dictionnaire plat contenant toutes les prédictions :

        Résultat 1X2 :
            home_win_proba, draw_proba, away_win_proba, predicted_result

        Score exact :
            predicted_home_score, predicted_away_score,
            exact_score_proba, top_scores

        Over/Under (seuils 0.5 / 1.5 / 2.5 / 3.5 / 4.5) :
            over_05_proba, under_05_proba, ..., over_45_proba, under_45_proba

        BTTS :
            btts_yes_proba, btts_no_proba

        Chance double :
            home_draw_proba, away_draw_proba, home_away_proba,
            predicted_double_chance

        Écart de buts :
            predicted_gap, predicted_gap_proba,
            signed_gap_probas, abs_gap_probas

        Métadonnées :
            matrix_sum (float) — doit être ≈ 1.0
    """
    return {
        # --- 1X2 ---
        **predict_result(matrix),
        # --- Score exact ---
        **predict_exact_score(matrix),
        # --- Over/Under ---
        **predict_total_goals(matrix),
        # --- BTTS ---
        **predict_btts(matrix),
        # --- Chance double ---
        **predict_double_chance(matrix),
        # --- Écart de buts ---
        **predict_goal_gap(matrix),
        # --- Diagnostic ---
        "matrix_sum": float(matrix.sum()),
    }


def predictions_to_db_row(predictions: dict) -> dict:
    """Sélectionne les champs qui correspondent aux colonnes de la table `predictions`.

    Extrait uniquement les clés compatibles avec le schéma Alembic
    (voir DATABASE_SCHEMA.md), en ignorant les champs enrichis comme
    top_scores ou signed_gap_probas.

    Args:
        predictions: Dict complet retourné par score_matrix_to_predictions().

    Returns:
        Dict prêt à insérer dans la table predictions via SQLAlchemy.
    """
    return {
        "home_win_proba": predictions.get("home_win_proba"),
        "draw_proba": predictions.get("draw_proba"),
        "away_win_proba": predictions.get("away_win_proba"),
        "predicted_home_score": predictions.get("predicted_home_score"),
        "predicted_away_score": predictions.get("predicted_away_score"),
        "exact_score_proba": predictions.get("exact_score_proba"),
        "over_05_proba": predictions.get("over_05_proba"),
        "over_15_proba": predictions.get("over_15_proba"),
        "over_25_proba": predictions.get("over_25_proba"),
        "over_35_proba": predictions.get("over_35_proba"),
        "over_45_proba": predictions.get("over_45_proba"),
        "btts_proba": predictions.get("btts_yes_proba"),
        "home_draw_proba": predictions.get("home_draw_proba"),
        "away_draw_proba": predictions.get("away_draw_proba"),
        "home_away_proba": predictions.get("home_away_proba"),
    }
