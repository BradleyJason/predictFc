"""Schemas Pydantic pour les matchs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamBrief(BaseModel):
    """Résumé d'une équipe dans le contexte d'un match."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    short_name: str | None = None


class MatchOut(BaseModel):
    """Réponse complète pour un match."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: int | None = None
    competition_id: int | None = None
    home_team_id: int | None = None
    away_team_id: int | None = None
    match_date: datetime
    status: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    matchday: int | None = None
    stage: str | None = None

    # Relations optionnelles (eager-loaded)
    home_team: TeamBrief | None = None
    away_team: TeamBrief | None = None


class MatchListOut(BaseModel):
    """Liste paginée de matchs."""

    matches: list[MatchOut]
    total: int
    skip: int
    limit: int
