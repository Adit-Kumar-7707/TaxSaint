"""Persisted tax calculation results."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from database_manager.connection import Base

class TaxResult(Base):
    __tablename__ = "tax_results"
    result_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    gross_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    taxable_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_before_cess: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cess: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
