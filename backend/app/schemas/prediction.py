"""Schemas Pydantic pour les prédictions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

DISCLAIMER = (
    "Ces prédictions sont basées sur des modèles statistiques. "
    "Aucune prédiction n'est garantie. Jouez responsablement "
    "et uniquement sur des plateformes agréées ANJ."
)


class TopScore(BaseModel):
    """Un score dans le top 5 des scores les plus probables."""

    home: int
    away: int
    proba: float


class PredictionOut(BaseModel):
    """Réponse complète des prédictions pour un match."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int | None = None
    model_version: str | None = None

    # 1X2
    home_win_proba: float | None = None
    draw_proba: float | None = None
    away_win_proba: float | None = None

    # Score exact
    predicted_home_score: int | None = None
    predicted_away_score: int | None = None
    exact_score_proba: float | None = None

    # Over/Under
    over_05_proba: float | None = None
    over_15_proba: float | None = None
    over_25_proba: float | None = None
    over_35_proba: float | None = None
    over_45_proba: float | None = None

    # BTTS
    btts_proba: float | None = None

    # Chance double
    home_draw_proba: float | None = None
    away_draw_proba: float | None = None
    home_away_proba: float | None = None

    # Qualification
    home_qualify_proba: float | None = None
    away_qualify_proba: float | None = None

    # Confiance
    confidence_score: int | None = None
    created_at: datetime | None = None

    # Champ enrichi non stocké en BDD (calculé à la volée)
    top_scores: list[TopScore] = Field(default_factory=list)

    # Disclaimer légal OBLIGATOIRE
    disclaimer: str = Field(default=DISCLAIMER)
