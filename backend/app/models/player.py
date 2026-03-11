"""SQLAlchemy model for players table."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Player(Base):
    """Représente un joueur de football."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str | None] = mapped_column(String(50))
    team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped["Team"] = relationship("Team", back_populates="players")  # noqa: F821
    stats: Mapped[list["PlayerStat"]] = relationship("PlayerStat", back_populates="player")  # noqa: F821

    def __repr__(self) -> str:
        """Représentation lisible."""
        return f"<Player {self.name}>"
