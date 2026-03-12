"""SQLAlchemy model for match_odds table."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class MatchOdds(Base):
    """Représente les cotes bookmakers pour un match."""
    __tablename__ = "match_odds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    bookmaker_id: Mapped[int | None] = mapped_column(Integer)
    bookmaker_name: Mapped[str | None] = mapped_column(String(50))

    home_win: Mapped[float | None] = mapped_column(Float)
    draw: Mapped[float | None] = mapped_column(Float)
    away_win: Mapped[float | None] = mapped_column(Float)

    # Cotes dérivées
    over_25: Mapped[float | None] = mapped_column(Float)
    under_25: Mapped[float | None] = mapped_column(Float)
    btts_yes: Mapped[float | None] = mapped_column(Float)
    btts_no: Mapped[float | None] = mapped_column(Float)

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    match: Mapped["Match"] = relationship("Match", back_populates="odds")  # noqa: F821

    def __repr__(self) -> str:
        return f"<MatchOdds match={self.match_id} {self.bookmaker_name} H={self.home_win} D={self.draw} A={self.away_win}>"