"""User creation and lookup endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database_manager.connection import get_db
from database_manager.models import User
from database_manager.repositories.user_repository import get_user
from integration.api.schemas.requests import UserCreate, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])

def serialize_user(user: User) -> dict:
    return {"id": user.user_id, "user_id": user.user_id, "name": user.name,
            "email": user.email, "phone": user.phone, "userType": user.worker_type.lower(),
            "worker_type": user.worker_type}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    worker_type = payload.user_type.upper()
    user = User(name=payload.name.strip(), email=payload.email.strip().lower(),
                phone=payload.phone, worker_type=worker_type)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A user with this email already exists.") from exc
    return serialize_user(user)

@router.get("/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return serialize_user(user)

@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    # Keep this as a profile update only; authentication credentials are not handled here.
    user.name = payload.name.strip()
    user.email = payload.email.strip().lower()
    user.phone = payload.phone
    user.worker_type = payload.user_type.upper()
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A user with this email already exists.") from exc
    return serialize_user(user)
