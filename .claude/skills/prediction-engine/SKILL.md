---
name: prediction-engine
description: Logique métier du moteur de prédictions PredictFC. Utiliser quand on travaille sur les prédictions (1X2, score exact, BTTS, etc.) ou le Smart Ticket.
---

# Prediction Engine — Conventions PredictFC

## Pipeline de prédiction
```
score_matrix (Double Poisson)
       │
       ├── result.py          → P(V_A), P(Nul), P(V_B)
       ├── total_goals.py     → P(Over/Under 0.5/1.5/2.5/3.5/4.5)
       ├── btts.py            → P(les deux équipes marquent)
       ├── exact_score.py     → Top 10 scores les plus probables
       ├── double_chance.py   → P(1X), P(X2), P(12)
       ├── goal_gap.py        → P(écart de 1, 2+, etc.)
       └── qualification.py   → Monte Carlo (10 000 simulations)
```

## Calculs depuis la matrice de scores
```python
# score_matrix[i][j] = P(equipe_A marque i buts, equipe_B marque j buts)

# 1X2
p_home_win = sum(score_matrix[i][j] for i in range(8) for j in range(8) if i > j)
p_draw     = sum(score_matrix[i][i] for i in range(8))
p_away_win = sum(score_matrix[i][j] for i in range(8) for j in range(8) if i < j)

# Over/Under
p_over_25  = sum(score_matrix[i][j] for i in range(8) for j in range(8) if i+j > 2)

# BTTS
p_btts     = sum(score_matrix[i][j] for i in range(1,8) for j in range(1,8))

# Chance double
p_1X = p_home_win + p_draw
p_X2 = p_draw + p_away_win
p_12 = p_home_win + p_away_win
```

## Smart Ticket — règles de sélection
```python
SEUIL_MIN_PROBA = 0.60      # 60% minimum par sélection
MAX_SELECTIONS = 3           # Maximum 3 paris combinés
SEUIL_CORRELATION = 0.70    # Alerter si corrélation > 70%

# Paris fortement corrélés à ne pas combiner
PARIS_CORRELES = [
    ("over_25", "btts"),           # corrélés à ~75%
    ("victoire_A", "chance_double_1X"),  # redondant
    ("victoire_B", "chance_double_X2"),  # redondant
]
```

## Score de confiance (0-100)
```python
def compute_confidence_score(
    data_quality: float,    # 0-1 : complétude des données
    model_stability: float, # 0-1 : variance du modèle sur ce type de match
    prediction_coherence: float,  # 0-1 : accord entre modèles
    match_volatility: float # 0-1 : imprévisibilité du match (derby, finale...)
) -> int:
    score = (data_quality * 0.3 +
             model_stability * 0.3 +
             prediction_coherence * 0.2 +
             (1 - match_volatility) * 0.2) * 100
    return int(score)
```

## Disclaimer légal — OBLIGATOIRE dans l'UI
```
"Ces prédictions sont basées sur des modèles statistiques.
Aucune prédiction n'est garantie. Jouez responsablement
et uniquement sur des plateformes agréées ANJ."
```
