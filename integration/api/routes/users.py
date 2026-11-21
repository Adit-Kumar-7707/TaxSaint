"""User registration, authentication, profile lookup, and update endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database_manager.connection import get_db
from database_manager.models import User
from database_manager.repositories.user_repository import get_user
from integration.api.auth import create_access_token, get_current_user, hash_password, verify_password
from integration.api.schemas.requests import TokenResponse, UserCreate, UserLogin, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


def serialize_user(user: User) -> dict:
    """Format user object for frontend consumption."""
    return {
        "id": user.user_id,
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "userType": user.worker_type.lower(),
        "worker_type": user.worker_type,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with optional password hashing."""
    worker_type = payload.user_type.upper()
    hashed_pwd = hash_password(payload.password) if payload.password else None

    user = User(
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
        phone=payload.phone,
        password=hashed_pwd,
        worker_type=worker_type
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        ) from exc

    token = create_access_token(user.user_id, user.email, user.worker_type)
    response_data = serialize_user(user)
    response_data["access_token"] = token
    response_data["token_type"] = "bearer"
    return response_data


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email and password; returns a signed Bearer token."""
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If account was created with a password, enforce verification
    if user.password:
        if not verify_password(payload.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    token = create_access_token(user.user_id, user.email, user.worker_type)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user)
    }


@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile using Bearer token."""
    return serialize_user(current_user)


@router.get("/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve user details by user ID (backward compatible)."""
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return serialize_user(user)


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    """Update profile details for an existing user."""
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    worker_type = payload.user_type.upper()
    user.name = payload.name.strip()
    user.email = payload.email.strip().lower()
    user.phone = payload.phone
    user.worker_type = worker_type

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        ) from exc

    return serialize_user(user)
