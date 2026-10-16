"""Imported bank transactions used to reconcile recorded income and expenses."""
from datetime import date
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from database_manager.connection import Base

class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (CheckConstraint("transaction_type IN ('INCOME', 'EXPENSE')", name="ck_bank_transaction_type"),)
    transaction_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    party_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
