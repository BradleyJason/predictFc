"""Schemas Pydantic pour le Smart Ticket."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.prediction import DISCLAIMER


class SmartTicketRequest(BaseModel):
    """Requête de génération d'un Smart Ticket."""

    match_ids: list[int] = Field(..., min_length=1, max_length=5)
    mode: Literal["simple", "combined"] = "simple"

    @field_validator("match_ids")
    @classmethod
    def no_duplicate_ids(cls, v: list[int]) -> list[int]:
        """Refuse les IDs dupliqués."""
        if len(v) != len(set(v)):
            raise ValueError("match_ids ne doit pas contenir de doublons.")
        return v


class SelectionItem(BaseModel):
    """Une sélection individuelle dans le ticket."""

    match_id: int
    prediction_id: int | None = None
    type: str          # ex: "home_win", "over_25", "btts_yes"
    label: str         # ex: "Victoire Domicile", "Plus de 2.5 buts"
    probability: float


class SmartTicketOut(BaseModel):
    """Réponse complète du Smart Ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    match_id: int | None = None
    prediction_id: int | None = None
    mode: str

    selections: list[SelectionItem]
    combined_proba: float | None = None
    confidence_score: int | None = None

    # Alerte si des paris corrélés ont été détectés et filtrés
    correlated_warning: bool = False

    # Disclaimer légal OBLIGATOIRE
    disclaimer: str = Field(default=DISCLAIMER)
