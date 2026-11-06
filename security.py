# Handles JWT creation and verification, and password hashing/validation for authentication.

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES"))

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in .env — server cannot start without it")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# hashes a plain text password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# verifies a plain text password against a stored hash
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# creates a signed JWT containing only the user_id — no password stored in token
def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# decodes and validates the JWT, raises 401 if invalid or expired
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

# extracts user_id from the bearer token — used as a FastAPI dependency in protected routes
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    payload = decode_token(credentials.credentials)
    return payload["sub"]
