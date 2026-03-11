"""PredictFC — Application FastAPI principale.

Lance avec :
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import matches_router, predictions_router, smart_ticket_router, stats_router
from app.core.config import settings

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PredictFC API",
    description=(
        "Prédictions de matchs de football basées sur des modèles statistiques. "
        "Ces prédictions ne sont pas garanties. Jouez responsablement."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_ALLOWED_ORIGINS = (
    [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Create React App / Next.js dev
        "http://localhost:8000",   # Backend self (Swagger UI)
    ]
    if settings.app_env == "development"
    else []  # En prod, origins configurées via env ou proxy
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

app.include_router(matches_router, prefix=API_PREFIX)
app.include_router(predictions_router, prefix=API_PREFIX)
app.include_router(smart_ticket_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Vérifie que l'API est opérationnelle.

    Returns:
        Statut OK avec la version et l'environnement courant.
    """
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }


@app.get("/", tags=["system"])
def root() -> dict:
    """Point d'entrée racine — redirige vers /docs."""
    return {"message": "PredictFC API — voir /docs pour la documentation."}
