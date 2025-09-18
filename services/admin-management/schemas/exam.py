"""
Exam and Subject Database Models
SQLAlchemy models for exam registry and subject management
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import Base


class ExamRegistry(Base):
    """Exam Registry Model"""
    __tablename__ = "exam_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    exam_type = Column(String(50), nullable=False)
    academic_year = Column(Integer, nullable=False)
    created_by_admin = Column(String(100), nullable=False)
    admin_key_hash = Column(String(500), nullable=False)
    status = Column(String(20), default='ACTIVE', nullable=False)
    total_subjects = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subjects = relationship("SubjectRegistry", back_populates="exam", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')", name='check_exam_status'),
        CheckConstraint("academic_year >= 2020 AND academic_year <= 2030", name='check_academic_year'),
    )

    def __repr__(self):
        return f"<ExamRegistry(exam_id='{self.exam_id}', name='{self.display_name}')>"


class SubjectRegistry(Base):
    """Subject Registry Model"""
    __tablename__ = "subject_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(String(150), unique=True, nullable=False, index=True)
    exam_id = Column(String(100), ForeignKey('exam_registry.exam_id', ondelete='CASCADE'), nullable=False)
    subject_code = Column(String(10), nullable=False)
    subject_name = Column(String(100), nullable=False)
    total_questions = Column(Integer, default=0)
    total_sheets = Column(Integer, default=0)
    folder_path = Column(String(500))
    status = Column(String(20), default='ACTIVE', nullable=False)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    exam = relationship("ExamRegistry", back_populates="subjects")
    sheets = relationship("QuestionSheet", back_populates="subject", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name='check_subject_status'),
        CheckConstraint("subject_code IN ('PHY', 'CHE', 'MAT', 'BIO', 'ENG')", name='check_subject_codes'),
    )

    def __repr__(self):
        return f"<SubjectRegistry(subject_id='{self.subject_id}', name='{self.subject_name}')>"


class QuestionSheet(Base):
    """Question Sheet Model"""
    __tablename__ = "question_sheets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_id = Column(String(200), unique=True, nullable=False, index=True)
    subject_id = Column(String(150), ForeignKey('subject_registry.subject_id', ondelete='CASCADE'), nullable=False)
    sheet_name = Column(String(200), nullable=False)
    file_path = Column(String(1000))
    version = Column(Integer, default=1)
    total_questions = Column(Integer, default=0)
    imported_questions = Column(Integer, default=0)
    failed_questions = Column(Integer, default=0)
    import_status = Column(String(30), default='PENDING')
    file_checksum = Column(String(128))
    last_imported_at = Column(TIMESTAMP(timezone=True))
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subject = relationship("SubjectRegistry", back_populates="sheets")
    questions = relationship("Question", back_populates="sheet", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("import_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL')",
                        name='check_import_status'),
    )

    def __repr__(self):
        return f"<QuestionSheet(sheet_id='{self.sheet_id}', name='{self.sheet_name}')>"


class Question(Base):
    """Question Model"""
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(String(250), unique=True, nullable=False, index=True)
    question_number = Column(String(20), nullable=False)
    sheet_id = Column(String(200), ForeignKey('question_sheets.sheet_id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(String(150), ForeignKey('subject_registry.subject_id'), nullable=False)

    # Question Content
    question_text = Column(Text)
    question_latex = Column(Text)
    question_type = Column(String(30), default='MCQ', nullable=False)

    # Classification
    difficulty_level = Column(Integer)  # 0.0 to 1.0
    topic_tags = Column(Text)  # Array of tags
    subtopic_tags = Column(Text)  # Array of subtopic tags

    # Answer Information
    correct_option = Column(String(10))
    numerical_answer = Column(Integer)
    explanation = Column(Text)
    explanation_latex = Column(Text)

    # Asset Information
    has_images = Column(Boolean, default=False)
    image_count = Column(Integer, default=0)

    # Import Metadata
    original_question_number = Column(String(20))
    import_source = Column(String(200))
    validation_status = Column(String(20), default='PENDING')
    confidence_score = Column(Integer, default=0.8)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sheet = relationship("QuestionSheet", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    assets = relationship("QuestionAsset", back_populates="question", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("question_type IN ('MCQ', 'NUMERICAL', 'ASSERTION_REASON', 'MATRIX_MATCH')",
                        name='check_question_type'),
        CheckConstraint("validation_status IN ('PENDING', 'VALIDATED', 'REJECTED', 'NEEDS_REVIEW')",
                        name='check_validation_status'),
    )

    def __repr__(self):
        return f"<Question(question_id='{self.question_id}', number='{self.question_number}')>"


class QuestionOption(Base):
    """Question Option Model"""
    __tablename__ = "question_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    option_id = Column(String(300), unique=True, nullable=False, index=True)
    question_id = Column(String(250), ForeignKey('questions.question_id', ondelete='CASCADE'), nullable=False)
    option_number = Column(Integer, nullable=False)
    option_text = Column(Text)
    option_latex = Column(Text)
    is_correct = Column(Boolean, default=False)
    has_image = Column(Boolean, default=False)
    image_reference = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    question = relationship("Question", back_populates="options")
    assets = relationship("QuestionAsset", back_populates="option", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("option_number BETWEEN 1 AND 4", name='check_option_number'),
    )

    def __repr__(self):
        return f"<QuestionOption(option_id='{self.option_id}', number={self.option_number})>"


class QuestionAsset(Base):
    """Question Asset Model"""
    __tablename__ = "question_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String(300), unique=True, nullable=False, index=True)
    question_id = Column(String(250), ForeignKey('questions.question_id', ondelete='CASCADE'))
    option_id = Column(String(300), ForeignKey('question_options.option_id', ondelete='CASCADE'))

    # Asset Properties
    asset_type = Column(String(20), nullable=False)
    asset_role = Column(String(30), nullable=False)

    # File Information
    original_filename = Column(String(500))
    storage_path = Column(String(1000))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))

    # Optimized Formats
    formats = Column(JSONB, default={})
    dimensions = Column(JSONB, default={})

    # Processing Status
    processing_status = Column(String(20), default='PENDING')
    optimization_level = Column(String(10), default='STANDARD')

    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    question = relationship("Question", back_populates="assets")
    option = relationship("QuestionOption", back_populates="assets")

    # Constraints
    __table_args__ = (
        CheckConstraint("asset_type IN ('IMAGE', 'DIAGRAM', 'GRAPH', 'TABLE', 'FORMULA')",
                        name='check_asset_type'),
        CheckConstraint("asset_role IN ('QUESTION_IMAGE', 'OPTION_IMAGE', 'EXPLANATION_IMAGE', 'COMPLETE_QUESTION')",
                        name='check_asset_role'),
        CheckConstraint("processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
                        name='check_processing_status'),
        CheckConstraint("optimization_level IN ('BASIC', 'STANDARD', 'HIGH')",
                        name='check_optimization_level'),
        CheckConstraint(
            "(question_id IS NOT NULL AND option_id IS NULL) OR (question_id IS NULL AND option_id IS NOT NULL)",
            name='check_asset_belongs_to_question_or_option'
        ),
    )

    def __repr__(self):
        return f"<QuestionAsset(asset_id='{self.asset_id}', type='{self.asset_type}')>"
