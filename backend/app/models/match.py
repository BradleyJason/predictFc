"""SQLAlchemy model for matches table."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Match(Base):
    """Représente un match de football."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    competition_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("competitions.id"))
    home_team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"))
    away_team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"))
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str | None] = mapped_column(String(20))
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    matchday: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    competition: Mapped["Competition"] = relationship("Competition", back_populates="matches")  # noqa: F821
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")  # noqa: F821
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")  # noqa: F821
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="match")  # noqa: F821
    player_stats: Mapped[list["PlayerStat"]] = relationship("PlayerStat", back_populates="match")  # noqa: F821
    smart_tickets: Mapped[list["SmartTicket"]] = relationship("SmartTicket", back_populates="match")  # noqa: F821

    def __repr__(self) -> str:
        """Représentation lisible."""
        return f"<Match {self.home_team_id} vs {self.away_team_id} ({self.match_date})>"
