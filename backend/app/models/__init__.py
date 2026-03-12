"""Modèles SQLAlchemy — exports centralisés."""
from app.models.competition import Competition
from app.models.season import Season
from app.models.team import Team
from app.models.match import Match
from app.models.match_stat import MatchStat
from app.models.match_event import MatchEvent
from app.models.match_odds import MatchOdds
from app.models.injury import Injury
from app.models.lineup import Lineup, LineupPlayer
from app.models.player import Player
from app.models.player_stat import PlayerStat
from app.models.prediction import Prediction
from app.models.smart_ticket import SmartTicket

__all__ = [
    "Competition", "Season", "Team", "Match",
    "MatchStat", "MatchEvent", "MatchOdds",
    "Injury", "Lineup", "LineupPlayer",
    "Player", "PlayerStat", "Prediction", "SmartTicket",
]