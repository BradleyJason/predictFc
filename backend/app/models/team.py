"""SQLAlchemy model for teams table."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Team(Base):
    """Représente une équipe de football."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50))
    competition_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("competitions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    competition: Mapped["Competition"] = relationship("Competition", back_populates="teams")  # noqa: F821
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")  # noqa: F821
    home_matches: Mapped[list["Match"]] = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")  # noqa: F821
    away_matches: Mapped[list["Match"]] = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")  # noqa: F821

    def __repr__(self) -> str:
        """Représentation lisible."""
        return f"<Team {self.name}>"
