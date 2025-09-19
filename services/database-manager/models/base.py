"""
Database Manager Models
Core system models for ID sequences, operations, and configuration
"""

from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import Base


class IDSequence(Base):
    """ID Sequence Model"""
    __tablename__ = "id_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_type = Column(String(50), nullable=False)
    sequence_key = Column(String(200), nullable=False)
    current_value = Column(Integer, default=0, nullable=False)
    prefix = Column(String(50))
    suffix = Column(String(50))
    format_template = Column(String(200))
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<IDSequence(type='{self.sequence_type}', key='{self.sequence_key}')>"


class ImportOperation(Base):
    """Import Operation Model"""
    __tablename__ = "import_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(String(100), unique=True, nullable=False)
    operation_type = Column(String(30), nullable=False)
    initiated_by = Column(String(100), nullable=False)
    source_file = Column(String(1000))
    target_subject_id = Column(String(150))
    status = Column(String(20), default='STARTED')
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_log = Column(Text)
    success_log = Column(Text)
    performance_metrics = Column(JSONB, default={})
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    duration_seconds = Column(Integer)

    def __repr__(self):
        return f"<ImportOperation(id='{self.operation_id}', type='{self.operation_type}')>"


class SystemConfiguration(Base):
    """System Configuration Model"""
    __tablename__ = "system_configuration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), nullable=False)
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)
    last_modified_by = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemConfiguration(key='{self.config_key}')>"
