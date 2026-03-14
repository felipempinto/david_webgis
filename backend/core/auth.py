import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from db.session import get_db
from models.user import User

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(user: User):
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)

    payload = {
        "sub": str(user.public_id),
        "exp": expire
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

#TODO: Preparar essa função
# def verify_token(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
#         username = payload.get("sub")

#         if username != APP_USERNAME:
#             raise HTTPException(status_code=401, detail="Invalid user")

#         return username

#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

        user_public_id = payload.get("sub")

        if user_public_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = (
            db.query(User)
            .filter(User.public_id == user_public_id)
            .first()
        )

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )