---
name: ml-pipeline
description: Conventions du pipeline ML PredictFC. Utiliser quand on travaille sur les modèles, le feature engineering, l'entraînement, ou l'évaluation des modèles.
---

# ML Pipeline — Conventions PredictFC

## Architecture des modèles
Tous les modèles héritent de BaseModel :
```python
from abc import ABC, abstractmethod
import numpy as np

class BaseModel(ABC):
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> None: ...
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray: ...
    
    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...
```

## Modèles disponibles
1. PoissonModel   → baseline, prédit distribution de scores P(i,j)
2. XGBoostModel   → classification 1X2 + régression buts
3. PlayerModel    → buteurs/passeurs probables (phase 3)

## La matrice de scores est le cœur du système
```python
# Toutes les prédictions se déduisent de score_matrix[i][j] = P(score_A=i, score_B=j)
# Taille recommandée : 8x8 (0 à 7 buts par équipe)
score_matrix = compute_score_matrix(lambda_home, lambda_away)  # Double Poisson
```

## MLflow — tracking obligatoire
```python
import mlflow

# Toujours tracker avec MLflow
with mlflow.start_run():
    mlflow.log_params({"model": "poisson", "competition": "PL"})
    mlflow.log_metrics({"accuracy": acc, "log_loss": loss})
    mlflow.sklearn.log_model(model, "model")
```

## DVC — pipeline déclaratif
Toujours déclarer les étapes dans ml/pipelines/dvc.yaml :
```yaml
stages:
  ingest:
    cmd: python pipelines/ingest.py
    deps: [pipelines/ingest.py]
    outs: [data/raw/matches.json]
  
  preprocess:
    cmd: python pipelines/preprocess.py
    deps: [pipelines/preprocess.py, data/raw/matches.json]
    outs: [data/processed/features.parquet]
  
  train:
    cmd: python pipelines/train.py
    deps: [pipelines/train.py, data/processed/features.parquet]
    params: [params.yaml]
    metrics: [metrics.json]
```

## Évaluation — métriques obligatoires
- accuracy (classification 1X2)
- log_loss (calibration des probabilités)
- brier_score (qualité des probabilités)
- backtesting sur au moins 1 saison complète

## Features obligatoires
- forme_domicile_5j : moyenne buts marqués sur 5 derniers matchs à domicile
- forme_exterieur_5j : idem à l'extérieur  
- buts_encaisses_moy : moyenne buts encaissés
- h2h_wins : % victoires en confrontations directes
- position_classement : position dans le classement
