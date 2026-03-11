"""Prédiction chance double à partir de la matrice de scores.

Trois marchés :
  1X (home_draw) : domicile gagne OU nul  → P(H) + P(D)
  X2 (away_draw) : extérieur gagne OU nul → P(D) + P(A)
  12 (home_away) : domicile OU extérieur  → P(H) + P(A)

Ces probabilités se déduisent directement des probabilités 1X2.
"""

import numpy as np

from engine.predictions.result import predict_result


def predict_double_chance(matrix: np.ndarray) -> dict:
    """Calcule les probabilités des trois marchés chance double.

    Args:
        matrix: Matrice (n, n) où matrix[i, j] = P(home=i, away=j).

    Returns:
        Dict avec :
            - home_draw_proba (float) : P(1X) = P(home win) + P(draw)
            - away_draw_proba (float) : P(X2) = P(draw) + P(away win)
            - home_away_proba (float) : P(12) = P(home win) + P(away win)
            - predicted_double_chance (str) : marché le plus probable ("1X", "X2" ou "12")
    """
    r = predict_result(matrix)
    home_win = r["home_win_proba"]
    draw = r["draw_proba"]
    away_win = r["away_win_proba"]

    home_draw = home_win + draw   # 1X
    away_draw = draw + away_win   # X2
    home_away = home_win + away_win  # 12

    best = max(
        [("1X", home_draw), ("X2", away_draw), ("12", home_away)],
        key=lambda x: x[1],
    )

    return {
        "home_draw_proba": home_draw,
        "away_draw_proba": away_draw,
        "home_away_proba": home_away,
        "predicted_double_chance": best[0],
    }
