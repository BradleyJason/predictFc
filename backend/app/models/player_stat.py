"""SQLAlchemy model for player_stats table."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlayerStat(Base):
    """Stats d'un joueur sur un match donné."""

    __tablename__ = "player_stats"
    __table_args__ = (UniqueConstraint("player_id", "match_id", name="uq_player_match"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"))
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"))
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    player: Mapped["Player"] = relationship("Player", back_populates="stats")  # noqa: F821
    match: Mapped["Match"] = relationship("Match", back_populates="player_stats")  # noqa: F821

    def __repr__(self) -> str:
        """Représentation lisible."""
        return f"<PlayerStat player={self.player_id} match={self.match_id}>"
