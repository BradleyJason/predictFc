"""PredictFC — Application FastAPI principale.
Lance avec :
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    enrichment_router,
    injuries_router,
    lineups_router,
    live_router,
    odds_router,
    matches_router,
    predictions_router,
    smart_ticket_router,
    stats_router,
)
from app.core.config import settings
from app.services.scheduler import create_scheduler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan : demarrage / arret du scheduler
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Demarre le scheduler au lancement, l'arrete proprement a la fermeture."""
    scheduler = create_scheduler()
    scheduler.start()
    logger.info(
        "Scheduler demarre — %d taches planifiees",
        len(scheduler.get_jobs()),
    )
    for job in scheduler.get_jobs():
        logger.info("  [job] %s | prochain : %s", job.name, job.next_run_time)

    yield  # L'application tourne ici

    scheduler.shutdown(wait=False)
    logger.info("Scheduler arrete.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PredictFC API",
    description=(
        "Predictions de matchs de football basees sur des modeles statistiques. "
        "Ces predictions ne sont pas garanties. Jouez responsablement."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_ALLOWED_ORIGINS = (
    [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    if settings.app_env == "development"
    else []
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(matches_router,      prefix=API_PREFIX)
app.include_router(predictions_router,  prefix=API_PREFIX)
app.include_router(smart_ticket_router, prefix=API_PREFIX)
app.include_router(stats_router,        prefix=API_PREFIX)
app.include_router(enrichment_router,   prefix=API_PREFIX)
app.include_router(injuries_router,     prefix=API_PREFIX)
app.include_router(lineups_router,      prefix=API_PREFIX)
app.include_router(live_router,         prefix=API_PREFIX)
app.include_router(odds_router,         prefix=API_PREFIX)

# ---------------------------------------------------------------------------
# Routes systeme
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }


@app.get("/", tags=["system"])
def root() -> dict:
    return {"message": "PredictFC API — voir /docs pour la documentation."}


@app.get("/scheduler/jobs", tags=["system"])
def list_scheduler_jobs() -> list:
    """Liste les taches planifiees et leur prochain declenchement."""
    from apscheduler.schedulers.background import BackgroundScheduler
    # On recupere le scheduler via l'app state si besoin
    # Pour l'instant on relit la config statique
    scheduler = create_scheduler()
    return [
        {
            "id":            job.id,
            "name":          job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else "N/A",
        }
        for job in scheduler.get_jobs()
    ]
