from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.session import get_db
from models.user import User, UserRole
from core.auth import create_access_token, get_current_user
from core.security import verify_password, hash_password

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

router = APIRouter(prefix="/auth")

@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.viewer
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "data": {
            "public_id": str(user.public_id),
            "email": user.email,
            "role": user.role
        }
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "public_id": str(current_user.public_id),
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }