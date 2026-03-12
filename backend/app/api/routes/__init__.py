"""Export les routers FastAPI."""
from app.api.routes.enrichment import router as enrichment_router
from app.api.routes.injuries import router as injuries_router
from app.api.routes.live import router as live_router
from app.api.routes.value_bets import router as value_bets_router
from app.api.routes.lineups import router as lineups_router
from app.api.routes.odds import router as odds_router
from app.api.routes.matches import router as matches_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.smart_ticket import router as smart_ticket_router
from app.api.routes.stats import router as stats_router

__all__ = [
    "enrichment_router",
    "injuries_router",
    "live_router",
    "value_bets_router",
    "lineups_router",
    "odds_router",
    "matches_router",
    "predictions_router",
    "smart_ticket_router",
    "stats_router",
]
