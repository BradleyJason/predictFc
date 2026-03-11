"""Pydantic schemas for the Smart Ticket endpoint."""
from typing import Optional

from pydantic import BaseModel, field_validator

DISCLAIMER = (
    "Ces prédictions sont basées sur des modèles statistiques. "
    "Aucune prédiction n'est garantie. Jouez responsablement "
    "et uniquement sur des plateformes agréées ANJ."
)


class SmartTicketRequest(BaseModel):
    """Input body for POST /smart-ticket."""

    match_ids: list[int]
    mode: str = "combined"

    @field_validator("match_ids")
    @classmethod
    def validate_match_ids(cls, v: list[int]) -> list[int]:
        """Require 1–10 match IDs."""
        if len(v) < 1:
            raise ValueError("Au moins un match est requis.")
        if len(v) > 10:
            raise ValueError("Maximum 10 matchs par ticket.")
        return v


class SelectionItem(BaseModel):
    """One selected bet within a smart ticket."""

    match_id: int
    bet_type: str
    label: str
    probability: float


class SmartTicketOut(BaseModel):
    """Generated smart ticket returned by the API."""

    selections: list[SelectionItem]
    combined_proba: float
    confidence_score: int
    mode: str
    correlated_warning: Optional[str] = None
    disclaimer: str = DISCLAIMER
