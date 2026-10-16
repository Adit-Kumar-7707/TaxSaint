"""User model for salaried employees and business owners."""
from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from database_manager.connection import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("worker_type IN ('SALARIED', 'BUSINESS')", name="ck_users_worker_type"),)

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    # Authentication is not implemented in this prototype; never store plaintext passwords.
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    worker_type: Mapped[str] = mapped_column(String(10), nullable=False)
