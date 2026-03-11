"""ORM model for the `smart_tickets` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.prediction import Prediction


class SmartTicket(Base):
    """Auto-generated combined betting ticket for one or more matches."""

    __tablename__ = "smart_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"))
    prediction_id: Mapped[int | None] = mapped_column(ForeignKey("predictions.id"))
    selections: Mapped[dict] = mapped_column(JSONB, nullable=False)
    combined_proba: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    mode: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    match: Mapped["Match | None"] = relationship("Match")
    prediction: Mapped["Prediction | None"] = relationship(
        "Prediction", back_populates="smart_tickets"
    )
