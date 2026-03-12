"""Pydantic schemas for match-related API responses."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CompetitionBrief(BaseModel):
    """Minimal competition info embedded in match responses."""
    id: int
    code: str
    name: str
    country: Optional[str] = None
    season: Optional[str] = None
    crest_url: Optional[str] = None
    model_config = {"from_attributes": True}

class TeamBrief(BaseModel):
    """Minimal team info embedded in match responses."""
    id: int
    external_id: Optional[int] = None
    name: str
    short_name: Optional[str] = None
    crest_url: Optional[str] = None
    model_config = {"from_attributes": True}


class MatchStatOut(BaseModel):
    """Stats d'une equipe pour un match (HOME ou AWAY)."""
    side: str
    shots_total: Optional[int] = None
    shots_on_goal: Optional[int] = None
    shots_off_goal: Optional[int] = None
    shots_blocked: Optional[int] = None
    ball_possession: Optional[float] = None
    passes_total: Optional[int] = None
    passes_accurate: Optional[int] = None
    passes_pct: Optional[float] = None
    corner_kicks: Optional[int] = None
    fouls: Optional[int] = None
    offsides: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    goalkeeper_saves: Optional[int] = None
    expected_goals: Optional[float] = None
    model_config = {"from_attributes": True}

class MatchOut(BaseModel):
    """Full match representation returned by the API."""
    id: int
    external_id: Optional[int] = None
    competition: Optional[CompetitionBrief] = None
    home_team: Optional[TeamBrief] = None
    away_team: Optional[TeamBrief] = None
    match_date: datetime
    status: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    matchday: Optional[int] = None
    stage: Optional[str] = None
    match_stats: list[MatchStatOut] = []
    model_config = {"from_attributes": True}

class MatchListItemOut(BaseModel):
    """Match dans une liste — sans match_stats pour eviter le joinedload sur collection."""
    id: int
    external_id: Optional[int] = None
    competition: Optional[CompetitionBrief] = None
    home_team: Optional[TeamBrief] = None
    away_team: Optional[TeamBrief] = None
    match_date: datetime
    status: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    matchday: Optional[int] = None
    stage: Optional[str] = None
    model_config = {"from_attributes": True}


class MatchListOut(BaseModel):
    """Paginated list of matches."""
    matches: list[MatchListItemOut]
    total: int
    skip: int
    limit: int
