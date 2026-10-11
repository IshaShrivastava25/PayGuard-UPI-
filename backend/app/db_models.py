from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="user")


class Prediction(Base):
    """One row per scored transaction. Doubles as the audit log: who scored what, when, with
    which model, and the exact explanation that was shown."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sender_vpa: Mapped[str] = mapped_column(String(100))
    receiver_vpa: Mapped[str] = mapped_column(String(100))
    tx_timestamp: Mapped[datetime] = mapped_column(DateTime)  # as entered, local time, no tz
    transaction_mode: Mapped[str] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Float)
    sender_balance_before: Mapped[float] = mapped_column(Float)
    sender_balance_after: Mapped[float] = mapped_column(Float)
    receiver_balance_before: Mapped[float] = mapped_column(Float)
    receiver_balance_after: Mapped[float] = mapped_column(Float)

    risk_score: Mapped[float] = mapped_column(Float)
    label: Mapped[str] = mapped_column(String(20), index=True)
    threshold: Mapped[float] = mapped_column(Float)
    model_name: Mapped[str] = mapped_column(String(50))
    model_variant: Mapped[str] = mapped_column(String(50))
    top_contributors: Mapped[list] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="predictions")
