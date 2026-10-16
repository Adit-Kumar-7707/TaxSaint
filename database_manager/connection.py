"""SQLAlchemy engine, session dependency, and local database initialization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_DATABASE = f"sqlite:///{PROJECT_ROOT / 'taxsaint.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DATABASE)

# Supabase commonly provides postgres:// or postgresql:// URLs. psycopg 3 is used.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite:"):
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


if DATABASE_URL.startswith("sqlite:"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        """Make SQLite enforce the same foreign keys as PostgreSQL."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """Yield a short-lived database session to a FastAPI route."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create missing tables and seed initial tax rules for a fresh database."""
    # Import models so SQLAlchemy registers all table definitions before create_all.
    from database_manager.models import (  # noqa: F401
        BankTransaction,
        Expense,
        FraudAlert,
        Income,
        TaxResult,
        TaxSettings,
        TaxSlab,
        User,
    )

    Base.metadata.create_all(bind=engine)

    # Seed only an empty tax-rule table. Existing rules are never overwritten.
    with SessionLocal() as db:
        if db.query(TaxSettings).count() == 0:
            db.add(TaxSettings(
                id=1,
                financial_year="2026-27",
                standard_deduction=75000,
                rebate_limit=1200000,
                cess_rate=4,
            ))
        if db.query(TaxSlab).count() == 0:
            db.add_all([
                TaxSlab(lower_limit=0, upper_limit=400000, rate=0),
                TaxSlab(lower_limit=400000, upper_limit=800000, rate=5),
                TaxSlab(lower_limit=800000, upper_limit=1200000, rate=10),
                TaxSlab(lower_limit=1200000, upper_limit=1600000, rate=15),
                TaxSlab(lower_limit=1600000, upper_limit=2000000, rate=20),
                TaxSlab(lower_limit=2000000, upper_limit=2400000, rate=25),
                TaxSlab(lower_limit=2400000, upper_limit=None, rate=30),
            ])
        db.commit()
