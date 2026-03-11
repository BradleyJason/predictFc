"""Pydantic schemas for prediction-related API responses."""
from typing import Optional

from pydantic import BaseModel

DISCLAIMER = (
    "Ces prédictions sont basées sur des modèles statistiques. "
    "Aucune prédiction n'est garantie. Jouez responsablement "
    "et uniquement sur des plateformes agréées ANJ."
)


class TopScore(BaseModel):
    """A single probable exact score with its probability."""

    home: int
    away: int
    probability: float


class PredictionOut(BaseModel):
    """Full prediction response for a match."""

    id: int
    match_id: Optional[int] = None
    model_version: Optional[str] = None

    # 1X2
    home_win_proba: Optional[float] = None
    draw_proba: Optional[float] = None
    away_win_proba: Optional[float] = None

    # Score exact
    predicted_home_score: Optional[float] = None
    predicted_away_score: Optional[float] = None
    exact_score_proba: Optional[float] = None

    # Over / Under
    over_05_proba: Optional[float] = None
    over_15_proba: Optional[float] = None
    over_25_proba: Optional[float] = None
    over_35_proba: Optional[float] = None
    over_45_proba: Optional[float] = None

    # BTTS
    btts_proba: Optional[float] = None

    # Double chance
    home_draw_proba: Optional[float] = None
    away_draw_proba: Optional[float] = None
    home_away_proba: Optional[float] = None

    # Qualification
    home_qualify_proba: Optional[float] = None
    away_qualify_proba: Optional[float] = None

    # Metadata
    confidence_score: Optional[int] = None
    top_scores: list[TopScore] = []
    disclaimer: str = DISCLAIMER

    model_config = {"from_attributes": True}
