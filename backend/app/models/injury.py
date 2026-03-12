"""SQLAlchemy model for injuries table."""
from datetime import datetime, date
from sqlalchemy import DateTime, Date, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Injury(Base):
    """Représente une blessure ou suspension d'un joueur."""
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"), index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"), index=True)
    season_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("seasons.id"), index=True)

    player_name: Mapped[str | None] = mapped_column(String(100))
    injury_type: Mapped[str | None] = mapped_column(String(50))   # Missing Fixture, Doubtful...
    reason: Mapped[str | None] = mapped_column(String(100))        # Ankle Injury, Suspension...

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    team: Mapped["Team"] = relationship("Team")  # noqa: F821
    match: Mapped["Match"] = relationship("Match", back_populates="injuries")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Injury {self.player_name} {self.injury_type} team={self.team_id}>"