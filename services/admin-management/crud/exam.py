"""
Exam CRUD Operations
Database operations for exam and subject management
"""

import os
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from datetime import datetime

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.security import security
from config.logging import logger
from services.database_manager.utils.id_generator import IndustryIDGenerator
from ..models.exam import ExamRegistry, SubjectRegistry, QuestionSheet
from ..schemas.exam import ExamCreate, ExamResponse, ExamListResponse, ExamStatistics

# Initialize ID generator
id_generator = IndustryIDGenerator()


def create_exam_with_subjects(db: Session, exam_data: ExamCreate, admin_id: str) -> ExamResponse:
    """
    Create a new exam with subjects
    """
    try:
        # Verify admin key
        if not security.verify_admin_key(exam_data.admin_key):
            raise ValueError("Invalid admin key")

        # Generate exam ID
        exam_id = id_generator.generate_exam_id(exam_data.academic_year, exam_data.exam_type.value)

        # Hash admin key for storage
        admin_key_hash = security.get_password_hash(exam_data.admin_key)

        # Create exam registry entry
        exam = ExamRegistry(
            exam_id=exam_id,
            display_name=exam_data.display_name,
            exam_type=exam_data.exam_type.value,
            academic_year=exam_data.academic_year,
            created_by_admin=admin_id,
            admin_key_hash=admin_key_hash,
            total_subjects=len(exam_data.subjects),
            status="ACTIVE",
            metadata={
                "created_by": admin_id,
                "creation_timestamp": datetime.utcnow().isoformat(),
                "initial_subjects": [s.subject_code.value for s in exam_data.subjects]
            }
        )

        db.add(exam)
        db.flush()  # To get the exam ID

        # Create subjects
        subjects = []
        for subject_data in exam_data.subjects:
            subject_id = id_generator.generate_subject_id(exam_id, subject_data.subject_code.value)
            folder_path = f"data/exam-registry/{exam_id}/subjects/{subject_data.subject_code.value.lower()}"

            subject = SubjectRegistry(
                subject_id=subject_id,
                exam_id=exam_id,
                subject_code=subject_data.subject_code.value,
                subject_name=subject_data.subject_name,
                folder_path=folder_path,
                status="ACTIVE",
                metadata={
                    "created_with_exam": True,
                    "folder_structure": {
                        "sheets": f"{folder_path}/sheets",
                        "assets": f"{folder_path}/assets",
                        "raw_assets": f"{folder_path}/assets/raw",
                        "processed_assets": f"{folder_path}/assets/processed"
                    }
                }
            )

            subjects.append(subject)
            db.add(subject)

        db.commit()

        # Refresh exam to get all relationships
        db.refresh(exam)

        logger.info(
            "Created exam with subjects",
            exam_id=exam_id,
            subjects_count=len(subjects),
            admin=admin_id
        )

        return ExamResponse(
            id=str(exam.id),
            exam_id=exam.exam_id,
            display_name=exam.display_name,
            exam_type=exam.exam_type,
            academic_year=exam.academic_year,
            status=exam.status,
            total_subjects=exam.total_subjects,
            total_questions=exam.total_questions,
            subjects=[
                {
                    "id": str(s.id),
                    "subject_id": s.subject_id,
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "total_questions": s.total_questions,
                    "total_sheets": s.total_sheets,
                    "folder_path": s.folder_path,
                    "status": s.status,
                    "created_at": s.created_at
                } for s in subjects
            ],
            created_at=exam.created_at,
            updated_at=exam.updated_at
        )

    except Exception as e:
        db.rollback()
        logger.error("Error creating exam", error=str(e))
        raise


def get_exam_by_id(db: Session, exam_id: str) -> Optional[ExamResponse]:
    """
    Get exam by ID with all subjects
    """
    try:
        exam = db.query(ExamRegistry).options(
            joinedload(ExamRegistry.subjects)
        ).filter(ExamRegistry.exam_id == exam_id).first()

        if not exam:
            return None

        return ExamResponse(
            id=str(exam.id),
            exam_id=exam.exam_id,
            display_name=exam.display_name,
            exam_type=exam.exam_type,
            academic_year=exam.academic_year,
            status=exam.status,
            total_subjects=exam.total_subjects,
            total_questions=exam.total_questions,
            subjects=[
                {
                    "id": str(s.id),
                    "subject_id": s.subject_id,
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "total_questions": s.total_questions,
                    "total_sheets": s.total_sheets,
                    "folder_path": s.folder_path,
                    "status": s.status,
                    "created_at": s.created_at
                } for s in exam.subjects
            ],
            created_at=exam.created_at,
            updated_at=exam.updated_at
        )

    except Exception as e:
        logger.error("Error retrieving exam", exam_id=exam_id, error=str(e))
        return None


def get_exams_list(db: Session, skip: int = 0, limit: int = 100) -> List[ExamListResponse]:
    """
    Get paginated list of exams
    """
    try:
        exams = db.query(ExamRegistry).order_by(
            desc(ExamRegistry.created_at)
        ).offset(skip).limit(limit).all()

        return [
            ExamListResponse(
                id=str(exam.id),
                exam_id=exam.exam_id,
                display_name=exam.display_name,
                exam_type=exam.exam_type,
                academic_year=exam.academic_year,
                status=exam.status,
                total_subjects=exam.total_subjects,
                total_questions=exam.total_questions,
                created_at=exam.created_at
            ) for exam in exams
        ]

    except Exception as e:
        logger.error("Error retrieving exams list", error=str(e))
        return []


def get_exam_statistics(db: Session, exam_id: str) -> Optional[ExamStatistics]:
    """
    Get comprehensive exam statistics
    """
    try:
        # This would typically use the exam_statistics view from the database
        # For now, we'll compute it manually
        exam = db.query(ExamRegistry).filter(ExamRegistry.exam_id == exam_id).first()
        if not exam:
            return None

        # Count subjects
        subjects_count = db.query(SubjectRegistry).filter(
            SubjectRegistry.exam_id == exam_id
        ).count()

        # Count sheets
        sheets_count = db.query(QuestionSheet).join(SubjectRegistry).filter(
            SubjectRegistry.exam_id == exam_id
        ).count()

        return ExamStatistics(
            exam_id=exam.exam_id,
            display_name=exam.display_name,
            total_subjects=subjects_count,
            total_sheets=sheets_count,
            total_questions=exam.total_questions,
            total_assets=0,  # Would be computed from assets table
            validated_questions=0,  # Would be computed from questions table
            questions_with_images=0,  # Would be computed from questions table
            average_difficulty=0.5  # Would be computed from questions table
        )

    except Exception as e:
        logger.error("Error computing exam statistics", exam_id=exam_id, error=str(e))
        return None


def update_exam_status(db: Session, exam_id: str, new_status: str) -> bool:
    """
    Update exam status
    """
    try:
        exam = db.query(ExamRegistry).filter(ExamRegistry.exam_id == exam_id).first()
        if not exam:
            return False

        exam.status = new_status
        exam.updated_at = datetime.utcnow()
        db.commit()

        return True

    except Exception as e:
        logger.error("Error updating exam status", exam_id=exam_id, error=str(e))
        db.rollback()
        return False


def delete_exam_by_id(db: Session, exam_id: str) -> bool:
    """
    Delete exam and all related data
    """
    try:
        exam = db.query(ExamRegistry).filter(ExamRegistry.exam_id == exam_id).first()
        if not exam:
            return False

        db.delete(exam)
        db.commit()

        return True

    except Exception as e:
        logger.error("Error deleting exam", exam_id=exam_id, error=str(e))
        db.rollback()
        return False


def create_exam_folders(exam_id: str, subject_codes: List[str]):
    """
    Create physical folder structure for exam
    """
    try:
        base_path = f"data/exam-registry/{exam_id}"
        os.makedirs(base_path, exist_ok=True)

        for subject_code in subject_codes:
            subject_path = f"{base_path}/subjects/{subject_code.lower()}"

            # Create directory structure
            directories = [
                f"{subject_path}/sheets",
                f"{subject_path}/assets/raw",
                f"{subject_path}/assets/processed"
            ]

            for directory in directories:
                os.makedirs(directory, exist_ok=True)

            # Create CSV template
            csv_template_path = f"{subject_path}/sheets/{subject_code.lower()}_questions.csv"
            create_csv_template(csv_template_path)

        logger.info("Created exam folder structure", exam_id=exam_id, subjects=subject_codes)

    except Exception as e:
        logger.error("Error creating exam folders", exam_id=exam_id, error=str(e))
        raise


def create_csv_template(file_path: str):
    """
    Create CSV template file with proper headers
    """
    try:
        csv_headers = [
            'question_number', 'question_text', 'question_latex',
            'option_1_text', 'option_1_latex', 'option_2_text', 'option_2_latex',
            'option_3_text', 'option_3_latex', 'option_4_text', 'option_4_latex',
            'correct_option_number', 'has_images', 'image_roles',
            'difficulty_level', 'question_type', 'year', 'exam_session'
        ]

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write(','.join(csv_headers) + '\n')

        logger.info("Created CSV template", file_path=file_path)

    except Exception as e:
        logger.error("Error creating CSV template", file_path=file_path, error=str(e))
        raise
