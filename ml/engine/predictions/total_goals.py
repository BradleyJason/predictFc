"""Prédiction total buts (Over/Under) à partir de la matrice de scores.

P(over N.5) = Σ_{i+j > N} P(i,j)
P(under N.5) = 1 - P(over N.5)

Seuils couverts : 0.5, 1.5, 2.5, 3.5, 4.5
"""

import numpy as np

_THRESHOLDS = [0.5, 1.5, 2.5, 3.5, 4.5]


def predict_total_goals(matrix: np.ndarray) -> dict:
    """Calcule les probabilités Over/Under pour chaque seuil.

    Args:
        matrix: Matrice (n, n) où matrix[i, j] = P(home=i, away=j).

    Returns:
        Dict avec pour chaque seuil T in {0.5, 1.5, 2.5, 3.5, 4.5} :
            - over_{T_str}_proba  : P(total buts > T)
            - under_{T_str}_proba : P(total buts ≤ T)
        ex : {"over_05_proba": 0.95, "under_05_proba": 0.05, ...}
    """
    n = matrix.shape[0]
    i_grid, j_grid = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    total_grid = i_grid + j_grid  # (n, n) : total de buts pour chaque case

    result: dict = {}
    for threshold in _THRESHOLDS:
        key = f"over_{str(threshold).replace('.', '')}_proba"
        over = float(matrix[total_grid > threshold].sum())
        under = float(1.0 - over)
        result[key] = over
        result[key.replace("over", "under")] = max(under, 0.0)

    return result
