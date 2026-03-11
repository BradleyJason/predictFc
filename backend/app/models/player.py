"""ORM model for the `players` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.player_stat import PlayerStat
    from app.models.team import Team


class Player(Base):
    """Football player belonging to a team."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str | None] = mapped_column(String(50))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    team: Mapped["Team | None"] = relationship("Team", back_populates="players")
    stats: Mapped[list["PlayerStat"]] = relationship("PlayerStat", back_populates="player")
