from fastapi import APIRouter, Depends
from core.auth import verify_token

router = APIRouter()

@router.get("/protected")
def protected_route(user: str = Depends(verify_token)):
    return {
        "message": "You are authenticated",
        "user": user
    }
