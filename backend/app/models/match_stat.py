"""SQLAlchemy model pour match_stats — stats enrichies via api-football (Phase 3B)."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MatchStat(Base):
    __tablename__ = "match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(4), nullable=False)

    shots_total: Mapped[int | None] = mapped_column(Integer)
    shots_on_goal: Mapped[int | None] = mapped_column(Integer)
    shots_off_goal: Mapped[int | None] = mapped_column(Integer)
    shots_blocked: Mapped[int | None] = mapped_column(Integer)

    ball_possession: Mapped[float | None] = mapped_column(Float)
    passes_total: Mapped[int | None] = mapped_column(Integer)
    passes_accurate: Mapped[int | None] = mapped_column(Integer)
    passes_pct: Mapped[float | None] = mapped_column(Float)

    corner_kicks: Mapped[int | None] = mapped_column(Integer)
    fouls: Mapped[int | None] = mapped_column(Integer)
    offsides: Mapped[int | None] = mapped_column(Integer)

    yellow_cards: Mapped[int | None] = mapped_column(Integer)
    red_cards: Mapped[int | None] = mapped_column(Integer)
    goalkeeper_saves: Mapped[int | None] = mapped_column(Integer)

    expected_goals: Mapped[float | None] = mapped_column(Float)
    api_football_fixture_id: Mapped[int | None] = mapped_column(Integer, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="match_stats")  # noqa: F821
    team: Mapped["Team"] = relationship("Team")  # noqa: F821

    def __repr__(self) -> str:
        return f"<MatchStat match={self.match_id} team={self.team_id} side={self.side}>"
