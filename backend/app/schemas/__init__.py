"""Pydantic schemas — exports centralisés."""

from app.schemas.match import MatchListOut, MatchOut, TeamBrief
from app.schemas.prediction import DISCLAIMER, PredictionOut, TopScore
from app.schemas.smart_ticket import SelectionItem, SmartTicketOut, SmartTicketRequest

__all__ = [
    "DISCLAIMER",
    "MatchListOut",
    "MatchOut",
    "PredictionOut",
    "SelectionItem",
    "SmartTicketOut",
    "SmartTicketRequest",
    "TeamBrief",
    "TopScore",
]
