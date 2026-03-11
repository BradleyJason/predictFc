"""ORM model for the `teams` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.competition import Competition
    from app.models.match import Match
    from app.models.player import Player


class Team(Base):
    """Football club, e.g. Paris Saint-Germain."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    competition: Mapped["Competition | None"] = relationship(
        "Competition", back_populates="teams"
    )
    home_matches: Mapped[list["Match"]] = relationship(
        "Match", foreign_keys="Match.home_team_id", back_populates="home_team"
    )
    away_matches: Mapped[list["Match"]] = relationship(
        "Match", foreign_keys="Match.away_team_id", back_populates="away_team"
    )
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")
