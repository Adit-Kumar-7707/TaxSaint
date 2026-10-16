"""Small query helpers for user records."""
from sqlalchemy.orm import Session
from database_manager.models import User

def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()

def create_user(db: Session, *, name: str, email: str, worker_type: str, phone: str | None = None) -> User:
    user = User(name=name.strip(), email=email.lower().strip(), worker_type=worker_type.upper(), phone=phone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
