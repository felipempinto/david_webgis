from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from core.auth import create_access_token

router = APIRouter()

APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    if data.username != APP_USERNAME or data.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token()

    return {
        "access_token": token,
        "token_type": "bearer"
    }
