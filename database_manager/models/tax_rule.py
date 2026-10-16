"""Database-stored tax settings and progressive tax slabs."""
from decimal import Decimal
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from database_manager.connection import Base

class TaxSettings(Base):
    __tablename__ = "tax_settings"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    financial_year: Mapped[str] = mapped_column(String(10), nullable=False, default="2026-27")
    standard_deduction: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rebate_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cess_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

class TaxSlab(Base):
    __tablename__ = "tax_slabs"
    slab_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lower_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    upper_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
