"""SQLAlchemy model for lineups table."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Lineup(Base):
    """Représente la composition officielle d'une équipe pour un match."""
    __tablename__ = "lineups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    formation: Mapped[str | None] = mapped_column(String(10))  # ex: "4-3-3"
    coach_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    match: Mapped["Match"] = relationship("Match", back_populates="lineups")  # noqa: F821
    team: Mapped["Team"] = relationship("Team")  # noqa: F821
    players: Mapped[list["LineupPlayer"]] = relationship("LineupPlayer", back_populates="lineup")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Lineup match={self.match_id} team={self.team_id} {self.formation}>"


class LineupPlayer(Base):
    """Représente un joueur dans une composition."""
    __tablename__ = "lineup_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lineup_id: Mapped[int] = mapped_column(Integer, ForeignKey("lineups.id"), nullable=False, index=True)
    player_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"))
    api_football_player_id: Mapped[int | None] = mapped_column(Integer)
    player_name: Mapped[str | None] = mapped_column(String(100))
    number: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[str | None] = mapped_column(String(5))   # G, D, M, F
    grid: Mapped[str | None] = mapped_column(String(10))       # ex: "1:1"
    is_starter: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    lineup: Mapped["Lineup"] = relationship("Lineup", back_populates="players")  # noqa: F821

    def __repr__(self) -> str:
        return f"<LineupPlayer {self.player_name} {self.position} starter={self.is_starter}>"