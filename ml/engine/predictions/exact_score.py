"""Prédiction du score exact à partir de la matrice de scores.

Le score le plus probable est la case (i, j) avec P(i, j) maximale.
On retourne également les 5 scores les plus probables pour affichage.
"""

import numpy as np


def predict_exact_score(matrix: np.ndarray) -> dict:
    """Identifie le score exact le plus probable et ses alternatives.

    Args:
        matrix: Matrice (n, n) où matrix[i, j] = P(home=i, away=j).

    Returns:
        Dict avec :
            - predicted_home_score (int) : buts domicile du score le plus probable
            - predicted_away_score (int) : buts extérieur du score le plus probable
            - exact_score_proba (float)  : probabilité du score le plus probable
            - top_scores (list[dict])    : 5 scores les plus probables avec leurs probas,
                chaque entrée : {"home": int, "away": int, "proba": float}
    """
    # Score le plus probable
    flat_idx = int(np.argmax(matrix))
    best_home, best_away = np.unravel_index(flat_idx, matrix.shape)

    # Top 5 scores
    flat_sorted = np.argsort(matrix.ravel())[::-1][:5]
    top_scores = []
    for idx in flat_sorted:
        h, a = np.unravel_index(idx, matrix.shape)
        top_scores.append(
            {"home": int(h), "away": int(a), "proba": float(matrix[h, a])}
        )

    return {
        "predicted_home_score": int(best_home),
        "predicted_away_score": int(best_away),
        "exact_score_proba": float(matrix[best_home, best_away]),
        "top_scores": top_scores,
    }
