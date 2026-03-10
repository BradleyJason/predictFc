---
name: football-data
description: Conventions pour interagir avec l'API football-data.org. Utiliser quand on travaille sur l'ingestion de données, les scripts de fetch, ou tout code qui appelle football-data.org
---

# Football Data API — Conventions PredictFC

## Base URL et authentification
```python
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": os.getenv("FOOTBALL_DATA_API_KEY")}
```

## Codes des compétitions supportées
```python
COMPETITIONS = {
    "ligue1": "FL1",
    "premier_league": "PL", 
    "champions_league": "CL",
    "la_liga": "PD",
    "bundesliga": "BL1",
    "serie_a": "SA"
}
```

## Endpoints principaux
```
GET /competitions/{code}/matches     → matchs d'une compétition
GET /competitions/{code}/standings   → classement
GET /matches/{id}                    → détail d'un match
GET /teams/{id}                      → détail d'une équipe
GET /persons/{id}                    → détail d'un joueur
```

## Règles importantes
- Rate limit : 10 requêtes/minute sur le plan gratuit
- Toujours gérer le rate limit avec un sleep(6) entre les requêtes
- Toujours logger les erreurs API dans le fichier de log
- Toujours versionner les données fetchées avec DVC après ingestion
- Stocker les données brutes dans ml/data/raw/ sans modification
- Format de fichier : JSON pour les données brutes, Parquet pour processed

## Pattern de fetch recommandé
```python
import time
import logging
from typing import Optional
import httpx

async def fetch_with_retry(url: str, headers: dict, max_retries: int = 3) -> Optional[dict]:
    """Fetch avec retry et respect du rate limit."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                time.sleep(6)  # Rate limit 10 req/min
                return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error {e.response.status_code}: {url}")
            if attempt == max_retries - 1:
                raise
    return None
```
