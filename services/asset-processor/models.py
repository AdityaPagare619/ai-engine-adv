"""
Asset Processor Models – SQLAlchemy definitions
"""
import uuid
from sqlalchemy import (
    Column, String, Integer, Boolean, JSON, TIMESTAMP, ForeignKey, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class QuestionAsset(Base):
    __tablename__ = "question_assets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String(300), unique=True, nullable=False)
    question_id = Column(String(250), nullable=False)
    asset_type = Column(String(20), nullable=False)
    asset_role = Column(String(30), nullable=False)
    original_filename = Column(String(500))
    storage_path = Column(String(1000))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(50))
    dimensions = Column(JSON, default={})
    formats = Column(JSON, default={})
    processing_status = Column(String(20), default="PENDING")
    optimization_level = Column(String(10), default="STANDARD")
    metadata = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
