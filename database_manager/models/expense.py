"""Expense rows entered by the user or imported from a statement."""
from datetime import date
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from database_manager.connection import Base

class Expense(Base):
    __tablename__ = "expenses"
    expense_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    party_name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
