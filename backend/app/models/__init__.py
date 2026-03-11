"""Re-export all ORM models so Alembic and other modules can import from one place."""
from app.models.competition import Competition
from app.models.match import Match
from app.models.player import Player
from app.models.player_stat import PlayerStat
from app.models.prediction import Prediction
from app.models.smart_ticket import SmartTicket
from app.models.team import Team

__all__ = [
    "Competition",
    "Team",
    "Player",
    "Match",
    "PlayerStat",
    "Prediction",
    "SmartTicket",
]
