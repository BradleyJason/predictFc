"""Prédiction du résultat 1X2 à partir de la matrice de scores.

P(home win) = Σ_{i>j} P(i,j)   → triangle inférieur de la matrice
P(draw)     = Σ_{i=j} P(i,i)   → diagonale principale
P(away win) = Σ_{i<j} P(i,j)   → triangle supérieur
"""

import numpy as np


def predict_result(matrix: np.ndarray) -> dict:
    """Calcule les probabilités 1X2 depuis la matrice de scores.

    Args:
        matrix: Matrice (n, n) où matrix[i, j] = P(home=i, away=j).

    Returns:
        Dict avec :
            - home_win_proba (float) : P(domicile gagne)
            - draw_proba (float)     : P(nul)
            - away_win_proba (float) : P(extérieur gagne)
            - predicted_result (str) : "H", "D" ou "A"
    """
    n = matrix.shape[0]
    indices = np.arange(n)

    # Masques triangulaires
    i_grid, j_grid = np.meshgrid(indices, indices, indexing="ij")
    home_win = float(matrix[i_grid > j_grid].sum())
    draw = float(np.trace(matrix))
    away_win = float(matrix[i_grid < j_grid].sum())

    # Équipe avec la probabilité la plus haute
    best = max(
        [("H", home_win), ("D", draw), ("A", away_win)],
        key=lambda x: x[1],
    )

    return {
        "home_win_proba": home_win,
        "draw_proba": draw,
        "away_win_proba": away_win,
        "predicted_result": best[0],
    }
