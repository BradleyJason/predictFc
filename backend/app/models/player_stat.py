"""ORM model for the `player_stats` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.player import Player


class PlayerStat(Base):
    """Per-match statistics for a player (goals, assists, minutes)."""

    __tablename__ = "player_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "match_id", name="uq_player_match"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"))
    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    player: Mapped["Player | None"] = relationship("Player", back_populates="stats")
    match: Mapped["Match | None"] = relationship("Match", back_populates="player_stats")
