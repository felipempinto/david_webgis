# models/user.py

from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
import enum

from db.base import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id =            Column(Integer, primary_key=True)
    public_id =     Column(UUID(as_uuid=True),unique=True, nullable=False, server_default=text("gen_random_uuid()"))
    email =         Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role =          Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    created_at =    Column(DateTime, server_default=func.now())

    projects =      relationship("Project", back_populates="user")