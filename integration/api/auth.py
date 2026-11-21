"""
Authentication and security helpers for TaxSaint.
Provides password hashing (PBKDF2-HMAC-SHA256), stateless signed tokens,
and FastAPI route protection dependencies. Zero external dependencies required.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database_manager.connection import get_db
from database_manager.models import User

# Secret key used for signing authentication tokens
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "taxsaint-production-secure-token-sign-key-2026")
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days validity
PBKDF2_ITERATIONS = 100_000

security_bearer = HTTPBearer(auto_error=False)


# --- 1. Password Hashing & Verification (PBKDF2-HMAC-SHA256) ---

def hash_password(password: str) -> str:
    """Generate a secure salted PBKDF2-HMAC-SHA256 password hash."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verify plain password against the stored salt$hash string."""
    if not plain_password or not hashed_password:
        return False
    try:
        salt, expected_hex = hashed_password.split("$", 1)
        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(computed_key.hex(), expected_hex)
    except Exception:
        return False


# --- 2. Signed Token Generation & Validation (HMAC-SHA256) ---

def create_access_token(user_id: int, email: str, worker_type: str) -> str:
    """Create a URL-safe signed authentication token."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": worker_type,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")
    
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    
    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict:
    """Validate token signature and expiry; return payload if valid."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Malformed token format.")
        
        payload_b64, sig_b64 = parts
        
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        pad_len = 4 - (len(sig_b64) % 4)
        sig_bytes = base64.urlsafe_b64decode(sig_b64 + ("=" * (pad_len % 4)))
        
        if not hmac.compare_digest(expected_sig, sig_bytes):
            raise ValueError("Signature mismatch.")
        
        pad_len = 4 - (len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + ("=" * (pad_len % 4)))
        payload = json.loads(payload_bytes.decode("utf-8"))
        
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token has expired.")
            
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired credentials: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# --- 3. FastAPI Dependencies ---

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Enforce token authentication on protected endpoints."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User belonging to token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication for endpoints that support both guest and logged-in users."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        return db.get(User, payload.get("sub"))
    except Exception:
        return None
