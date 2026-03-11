"""Export les routers FastAPI."""
from app.api.routes.matches import router as matches_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.smart_ticket import router as smart_ticket_router
from app.api.routes.stats import router as stats_router

__all__ = ["matches_router", "predictions_router", "smart_ticket_router", "stats_router"]
