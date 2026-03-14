# models/dataset.py

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from db.base import Base


class Dataset(Base):

    __tablename__ = "datasets"

    id =            Column(Integer, primary_key=True)

    public_id =     Column(UUID(as_uuid=True), unique=True, nullable=False, server_default=text("gen_random_uuid()"))
    name =          Column(String, nullable=False)
    file_path =     Column(String, nullable=False)
    file_type =     Column(String)  # csv, geojson, etc
    meta =          Column(JSON)  # ou dataset_metadata
    project_id =    Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at =    Column(DateTime, server_default=func.now())

    project =       relationship("Project", back_populates="datasets")