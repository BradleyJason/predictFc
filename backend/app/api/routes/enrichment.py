"""Routes d'enrichissement des stats via api-football (Phase 3B)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.api_football_client import api_football_client
from app.services.enrichment_service import enrich_match, enrich_recent_matches

router = APIRouter(tags=["enrichment"])


@router.post("/enrichment/match/{match_id}")
def enrich_single_match(match_id: int, db: Session = Depends(get_db)) -> dict:
    """Enrichit un match spécifique avec les stats api-football."""
    try:
        success = enrich_match(match_id, db)
        if success:
            return {"status": "ok", "match_id": match_id}
        raise HTTPException(status_code=422, detail="Enrichissement impossible pour ce match.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/enrichment/recent")
def enrich_recent(limit: int = 10, db: Session = Depends(get_db)) -> dict:
    """Enrichit les matchs FINISHED récents non encore enrichis.

    Args:
        limit: Nombre max de matchs (défaut 10 ≈ 30 requêtes API).
    """
    if limit > 20:
        raise HTTPException(status_code=400, detail="Limite max : 20 matchs par appel.")
    results = enrich_recent_matches(db, limit=limit)
    return {"status": "ok", **results}


@router.get("/enrichment/quota")
def get_quota() -> dict:
    """Vérifie le quota api-football restant."""
    try:
        return api_football_client.check_status()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
