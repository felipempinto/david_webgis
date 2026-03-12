from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
from geoalchemy2 import Geometry

from db.base import Base

class Project(Base):

    __tablename__ = "projects"

    id =            Column(Integer, primary_key=True)
    public_id =     Column(UUID(as_uuid=True), unique=True, nullable=False, server_default=text("gen_random_uuid()"))
    name =          Column(String(100), nullable=False)
    user_id =       Column(Integer,ForeignKey("users.id"),nullable=False)
    geom =          Column(Geometry("MULTIPOLYGON", srid=4326))
    created_at =    Column(DateTime, server_default=func.now())

    user =          relationship("User", back_populates="projects")
    datasets =      relationship("Dataset", back_populates="project", cascade="all, delete")