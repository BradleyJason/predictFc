"""ORM model for the `competitions` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.team import Team


class Competition(Base):
    """Football competition (league or cup), e.g. Ligue 1, Premier League."""

    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(50))
    season: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    teams: Mapped[list["Team"]] = relationship("Team", back_populates="competition")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="competition")
