import sys
import os

sys.path.append(os.getcwd())

from db.session import SessionLocal

# IMPORTANTE: registrar models
from models.user import User, UserRole
from models.project import Project
from models.dataset import Dataset

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_admin():
    db = SessionLocal()

    email = "admin@platform.com"
    password = "admin123"

    existing = db.query(User).filter(User.email == email).first()

    if existing:
        print("Admin already exists")
        return

    admin = User(
        email=email,
        password_hash=get_password_hash(password),
        role=UserRole.admin
    )

    db.add(admin)
    db.commit()

    print("Admin created successfully")


if __name__ == "__main__":
    create_admin()