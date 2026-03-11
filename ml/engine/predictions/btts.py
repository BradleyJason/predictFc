"""Prédiction BTTS (Both Teams To Score) à partir de la matrice de scores.

P(BTTS yes) = Σ_{i>0, j>0} P(i,j)
            = 1 - P(home=0) - P(away=0) + P(home=0, away=0)

Les deux équipes marquent si et seulement si home_score ≥ 1 ET away_score ≥ 1.
"""

import numpy as np


def predict_btts(matrix: np.ndarray) -> dict:
    """Calcule la probabilité BTTS depuis la matrice de scores.

    Args:
        matrix: Matrice (n, n) où matrix[i, j] = P(home=i, away=j).

    Returns:
        Dict avec :
            - btts_yes_proba (float) : P(les deux équipes marquent)
            - btts_no_proba (float)  : P(au moins une équipe ne marque pas)
    """
    # Sous-matrice [1:, 1:] = tous les cas où les deux équipes marquent
    btts_yes = float(matrix[1:, 1:].sum())
    btts_no = float(1.0 - btts_yes)

    return {
        "btts_yes_proba": btts_yes,
        "btts_no_proba": max(btts_no, 0.0),
    }
