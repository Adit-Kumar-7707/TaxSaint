"""Potential anomaly alerts. An alert is not a confirmed finding of fraud."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from database_manager.connection import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    __table_args__ = (
        CheckConstraint("fraud_type IN ('DUPLICATE_EXPENSE', 'INCOME_MISMATCH')", name="ck_fraud_type"),
        CheckConstraint("transaction_source IN ('EXPENSE', 'INCOME', 'BANK')", name="ck_fraud_source"),
        CheckConstraint("status IN ('NEEDS_VERIFICATION', 'VERIFIED', 'DISMISSED')", name="ck_fraud_status"),
        UniqueConstraint("fraud_type", "transaction_source", "transaction_id", name="uq_fraud_alert_source"),
    )
    alert_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    fraud_type: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_source: Mapped[str] = mapped_column(String(10), nullable=False)
    transaction_id: Mapped[int] = mapped_column(nullable=False)
    matched_source: Mapped[str | None] = mapped_column(String(10), nullable=True)
    matched_transaction_id: Mapped[int | None] = mapped_column(nullable=True)
    difference_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEEDS_VERIFICATION")
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
