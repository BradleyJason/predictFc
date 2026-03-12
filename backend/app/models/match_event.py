"""SQLAlchemy model for match_events table."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class MatchEvent(Base):
    """Représente un événement dans un match (but, carton, remplacement)."""
    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teams.id"), index=True)
    player_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"))
    assist_player_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("players.id"))

    minute: Mapped[int | None] = mapped_column(Integer)
    extra_minute: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # Goal, Card, subst
    event_detail: Mapped[str | None] = mapped_column(String(50))  # Normal Goal, Yellow Card...
    comments: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    match: Mapped["Match"] = relationship("Match", back_populates="events")  # noqa: F821
    team: Mapped["Team"] = relationship("Team")  # noqa: F821

    def __repr__(self) -> str:
        return f"<MatchEvent {self.event_type} {self.minute}min match={self.match_id}>"