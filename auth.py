# Defines the /auth/register and /auth/login routes for user creation and token generation.

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from database import get_db
from security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth")

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

# validates email format, hashes password, inserts user into db — returns 400 if email already exists
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: AuthRequest):
    with get_db() as (_, cursor):
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (data.email, hash_password(data.password))
        )

    return {"message": "User created successfully"}

# looks up user by email, verifies hashed password, issues a JWT — 401 if user missing or password mismatch
@router.post("/login", status_code=status.HTTP_200_OK)
def login(data: AuthRequest):
    with get_db() as (_, cursor):
        cursor.execute("SELECT id, password FROM users WHERE email = %s", (data.email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["id"]))
    return {"access_token": token, "token_type": "bearer"}
