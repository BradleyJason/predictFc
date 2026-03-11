"""Prédiction de l'écart de buts à partir de la matrice de scores.

Écart signé  : home_score - away_score
  > 0 → victoire domicile par cet écart
  = 0 → match nul
  < 0 → victoire extérieur par cet écart

P(gap = k) = Σ_{i - j = k} P(i, j)   pour k dans [-max_goals, +max_goals]

On retourne également les probabilités d'écart absolu :
P(|gap| = k) = P(gap = k) + P(gap = -k)  pour k > 0
P(|gap| = 0) = P(gap = 0)
"""

import numpy as np


def predict_goal_gap(matrix: np.ndarray) -> dict:
    """Calcule la distribution de l'écart de buts.

    Args:
        matrix: Matrice (n, n) où matrix[i, j] = P(home=i, away=j).

    Returns:
        Dict avec :
            - predicted_gap (int)            : écart signé le plus probable (home - away)
            - predicted_gap_proba (float)    : probabilité de cet écart
            - signed_gap_probas (dict)       : {gap: proba} pour tous les écarts signés
            - abs_gap_probas (dict)          : {|gap|: proba} pour les écarts absolus
    """
    n = matrix.shape[0]
    max_gap = n - 1

    # Diagonales : chaque diagonale k correspond à home - away = k
    # np.diagonal(matrix, offset=k) donne les P(i, i-k) → home - away = k
    signed_gap: dict[int, float] = {}
    for k in range(-max_gap, max_gap + 1):
        diag = np.diagonal(matrix, offset=k)  # home - away = k
        signed_gap[k] = float(diag.sum())

    # Écart absolu
    abs_gap: dict[int, float] = {}
    abs_gap[0] = signed_gap[0]
    for k in range(1, max_gap + 1):
        abs_gap[k] = signed_gap.get(k, 0.0) + signed_gap.get(-k, 0.0)

    best_gap = max(signed_gap, key=signed_gap.__getitem__)

    return {
        "predicted_gap": best_gap,
        "predicted_gap_proba": signed_gap[best_gap],
        "signed_gap_probas": signed_gap,
        "abs_gap_probas": abs_gap,
    }
