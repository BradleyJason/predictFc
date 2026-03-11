"""API routes — exports des routers."""

from app.api.routes.matches import router as matches_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.smart_ticket import router as smart_ticket_router

__all__ = ["matches_router", "predictions_router", "smart_ticket_router"]
