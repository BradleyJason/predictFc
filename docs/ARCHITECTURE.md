# PredictFC — Architecture Technique

## Vue d'ensemble
```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                               │
│              React + TailwindCSS + Recharts                 │
│                    (Vite — port 5173)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────────┐
│                      BACKEND                                │
│                FastAPI (port 8000)                          │
│         SQLAlchemy + Alembic + Pydantic                     │
└──────┬───────────────────────────┬──────────────────────────┘
       │                           │
┌──────▼──────┐          ┌─────────▼──────────┐
│  ML Engine  │          │   Supabase          │
│  Poisson    │          │   (PostgreSQL)      │
│  XGBoost    │          │                     │
└──────┬──────┘          └────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│              DagsHub                        │
│     MLflow (experiments) + DVC (data)       │
└─────────────────────────────────────────────┘
```

## Stack technique

| Couche | Outil | Version |
|--------|-------|---------|
| Backend | FastAPI | 0.135.x |
| ORM | SQLAlchemy | 2.0.x |
| Migrations | Alembic | 1.18.x |
| BDD | Supabase (PostgreSQL) | - |
| ML baseline | scipy (Double Poisson) | 1.17.x |
| ML avancé | XGBoost | 3.2.x |
| ML pipeline | scikit-learn | 1.8.x |
| Tracking | MLflow | 2.x |
| Versioning data | DVC | 3.x |
| Hub ML | DagsHub | - |
| Frontend | React + Vite | 19 + 7 |
| CSS | TailwindCSS | 4.x |
| Graphes | Recharts | 3.x |
| Dépendances | Poetry | - |
| Tests backend | pytest | 9.x |
| Lint | ruff | 0.15.x |
| CI/CD | GitHub Actions | - |
| Conteneurs | Docker + docker-compose | - |
| Hébergement | Render | - |

## Modules principaux

### Backend (backend/app/)
```
api/routes/
  matches.py        → GET /api/matches
  predictions.py    → POST /api/predictions
  smart_ticket.py   → POST /api/smart-ticket
  players.py        → GET /api/players

core/
  database.py       → Connexion Supabase/SQLAlchemy
  security.py       → Auth basique

models/             → Modèles SQLAlchemy (tables BDD)
schemas/            → Schémas Pydantic (validation)
services/
  football_api.py   → Client football-data.org
  prediction_service.py → Orchestration prédictions
```

### ML (ml/)
```
pipelines/
  ingest.py         → Fetch données football-data.org
  preprocess.py     → Feature engineering
  train.py          → Entraînement modèles
  evaluate.py       → Backtesting + métriques
  dvc.yaml          → Pipeline DVC déclaratif

models/
  base_model.py     → Interface commune (ABC)
  poisson_model.py  → Double Poisson (baseline)
  xgboost_model.py  → XGBoost (amélioration)
  player_model.py   → Buteurs/passeurs (phase 3)

engine/
  score_matrix.py   → Matrice P(i,j) via Double Poisson
  predictions/      → 7 types de prédictions
  smart_ticket/     → Sélection optimale + corrélations
```

## Pipeline de prédiction
```
1. score_matrix = Double_Poisson(lambda_home, lambda_away)
   → Matrice 8x8 : P(score_A=i, score_B=j)

2. Depuis la matrice, on dérive :
   → 1X2          : somme triangles
   → Over/Under   : somme diagonales i+j > seuil
   → BTTS         : somme i>0 ET j>0
   → Score exact  : top 10 cases
   → Chance double: combinaisons 1X2
   → Écart buts   : diagonales parallèles
   → Qualification: Monte Carlo 10 000 simulations

3. Smart Ticket :
   → Filtre proba > 60%
   → Vérifie corrélations
   → Max 3 sélections
   → Score de confiance 0-100
```

## Flux de données
```
football-data.org API
       ↓
ml/pipelines/ingest.py
       ↓ (DVC tracked)
ml/data/raw/          → JSON bruts
       ↓
ml/pipelines/preprocess.py
       ↓ (DVC tracked)
ml/data/processed/    → Parquet features
       ↓
ml/pipelines/train.py → MLflow tracking
       ↓
Modèle enregistré dans MLflow Registry
       ↓
backend/services/prediction_service.py
       ↓
FastAPI endpoints
       ↓
React Frontend
```

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| APP_ENV | development / staging / production |
| DATABASE_URL | PostgreSQL connection string |
| SUPABASE_URL | URL du projet Supabase |
| SUPABASE_ANON_KEY | Clé publique Supabase |
| SUPABASE_SERVICE_KEY | Clé secrète Supabase |
| FOOTBALL_DATA_API_KEY | Clé API football-data.org |
| MLFLOW_TRACKING_URI | URI MLflow sur DagsHub |
| DAGSHUB_TOKEN | Token DagsHub |
| DVC_REMOTE_URL | URL remote DVC sur DagsHub |
