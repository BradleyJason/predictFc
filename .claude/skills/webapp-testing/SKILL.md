---
name: webapp-testing
description: Conventions de tests pour PredictFC. Utiliser quand on écrit des tests unitaires, d'intégration ou des tests UI avec Playwright.
---

# Webapp Testing — Conventions PredictFC

## Stack de tests
- Backend : pytest + pytest-cov (coverage minimum 80%)
- API : httpx (TestClient FastAPI)
- Frontend : Playwright
- Lint : ruff

## Structure des tests backend
```
backend/tests/
├── conftest.py          → fixtures partagées (DB test, client API)
├── test_api/
│   ├── test_predictions.py
│   └── test_smart_ticket.py
└── test_services/
    └── test_football_api.py
```

## Pattern de test API FastAPI
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_prediction_1x2():
    response = client.post("/api/predictions", json={
        "home_team_id": 1,
        "away_team_id": 2,
        "competition": "PL"
    })
    assert response.status_code == 200
    data = response.json()
    assert "home_win" in data
    assert "draw" in data
    assert "away_win" in data
    # Les probabilités doivent sommer à ~1
    total = data["home_win"] + data["draw"] + data["away_win"]
    assert abs(total - 1.0) < 0.01
```

## Pattern de test ML
```python
import numpy as np
from ml.engine.score_matrix import compute_score_matrix

def test_score_matrix_sums_to_one():
    matrix = compute_score_matrix(lambda_home=1.5, lambda_away=1.0)
    assert abs(matrix.sum() - 1.0) < 0.001

def test_probabilities_between_zero_and_one():
    matrix = compute_score_matrix(lambda_home=1.5, lambda_away=1.0)
    assert (matrix >= 0).all()
    assert (matrix <= 1).all()
```

## Commandes
```bash
# Lancer tous les tests
make test

# Tests avec coverage
cd backend && poetry run pytest --cov=app --cov-report=term-missing

# Lint
make lint
```
