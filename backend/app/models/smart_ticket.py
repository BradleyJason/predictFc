"""SQLAlchemy model for smart_tickets table."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SmartTicket(Base):
    """Combiné optimal généré automatiquement à partir des prédictions."""

    __tablename__ = "smart_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"))
    prediction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("predictions.id"))
    # selections: liste de dicts [{type, value, proba}]
    selections: Mapped[dict] = mapped_column(JSONB, nullable=False)
    combined_proba: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    mode: Mapped[str | None] = mapped_column(String(20))  # simple, combined
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    match: Mapped["Match"] = relationship("Match", back_populates="smart_tickets")  # noqa: F821
    prediction: Mapped["Prediction"] = relationship(  # noqa: F821
        "Prediction", back_populates="smart_tickets"
    )

    def __repr__(self) -> str:
        """Représentation lisible du modèle."""
        return f"<SmartTicket match={self.match_id} proba={self.combined_proba:.2f}>"
