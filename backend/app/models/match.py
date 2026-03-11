"""ORM model for the `matches` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.competition import Competition
    from app.models.player_stat import PlayerStat
    from app.models.prediction import Prediction
    from app.models.team import Team


class Match(Base):
    """A football match between two teams."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"))
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    match_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str | None] = mapped_column(String(20))
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    matchday: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    competition: Mapped["Competition | None"] = relationship(
        "Competition", back_populates="matches"
    )
    home_team: Mapped["Team | None"] = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_matches"
    )
    away_team: Mapped["Team | None"] = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_matches"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="match"
    )
    player_stats: Mapped[list["PlayerStat"]] = relationship(
        "PlayerStat", back_populates="match"
    )
