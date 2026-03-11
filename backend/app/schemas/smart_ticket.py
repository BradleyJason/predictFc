"""Pydantic schemas for the Smart Ticket endpoint."""
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.prediction import DISCLAIMER


class SmartTicketRequest(BaseModel):
    """Input body for POST /smart-ticket."""
    match_ids: list[int] = Field(..., min_length=1, max_length=5)
    mode: Literal["simple", "combined"] = "combined"

    @field_validator("match_ids")
    @classmethod
    def validate_match_ids(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("match_ids ne doit pas contenir de doublons.")
        return v


class SelectionItem(BaseModel):
    """One selected bet within a smart ticket."""
    match_id: int
    prediction_id: Optional[int] = None
    bet_type: str
    label: str
    probability: float


class SmartTicketOut(BaseModel):
    """Generated smart ticket returned by the API."""
    id: Optional[int] = None
    match_id: Optional[int] = None
    prediction_id: Optional[int] = None
    selections: list[SelectionItem]
    combined_proba: Optional[float] = None
    confidence_score: Optional[int] = None
    mode: str
    correlated_warning: Optional[str] = None
    disclaimer: str = Field(default=DISCLAIMER)
