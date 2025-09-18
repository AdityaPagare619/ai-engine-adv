"""
Exam Management Router
Handles exam creation, listing, and management operations
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import get_db
from config.logging import logger
from ..schemas.exam import ExamCreate, ExamResponse, ExamListResponse, ExamStatistics, SuccessResponse
from ..schemas.admin import AdminResponse
from ..security.auth import get_current_admin
from ..crud.exam import (
    create_exam_with_subjects,
    get_exam_by_id,
    get_exams_list,
    get_exam_statistics,
    delete_exam_by_id,
    update_exam_status
)

exam_router = APIRouter()


@exam_router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_exam(
        exam_data: ExamCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Create a new exam with subjects and folder structure
    """
    try:
        logger.info(
            "Creating new exam",
            exam_type=exam_data.exam_type,
            academic_year=exam_data.academic_year,
            admin=current_admin.admin_id
        )

        # Create exam and subjects
        exam = create_exam_with_subjects(db, exam_data, current_admin.admin_id)

        # Schedule folder creation in background
        background_tasks.add_task(
            create_exam_folder_structure,
            exam.exam_id,
            [subject.subject_code for subject in exam_data.subjects]
        )

        logger.info(
            "Exam created successfully",
            exam_id=exam.exam_id,
            total_subjects=len(exam.subjects)
        )

        return exam

    except ValueError as e:
        logger.error("Validation error creating exam", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error creating exam", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam"
        )


@exam_router.get("/", response_model=List[ExamListResponse])
async def list_exams(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Get list of all exams
    """
    try:
        exams = get_exams_list(db, skip=skip, limit=limit)

        logger.info(
            "Retrieved exams list",
            count=len(exams),
            admin=current_admin.admin_id
        )

        return exams

    except Exception as e:
        logger.error("Error retrieving exams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exams"
        )


@exam_router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam_details(
        exam_id: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Get detailed information about a specific exam
    """
    try:
        exam = get_exam_by_id(db, exam_id)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found"
            )

        logger.info(
            "Retrieved exam details",
            exam_id=exam_id,
            admin=current_admin.admin_id
        )

        return exam

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving exam", exam_id=exam_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exam"
        )


@exam_router.get("/{exam_id}/statistics", response_model=ExamStatistics)
async def get_exam_stats(
        exam_id: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Get comprehensive statistics for an exam
    """
    try:
        stats = get_exam_statistics(db, exam_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found"
            )

        logger.info(
            "Retrieved exam statistics",
            exam_id=exam_id,
            total_questions=stats.total_questions,
            admin=current_admin.admin_id
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving exam statistics", exam_id=exam_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exam statistics"
        )


@exam_router.put("/{exam_id}/status", response_model=SuccessResponse)
async def update_exam_status_endpoint(
        exam_id: str,
        status_value: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Update exam status (ACTIVE, INACTIVE, ARCHIVED)
    """
    try:
        if status_value not in ['ACTIVE', 'INACTIVE', 'ARCHIVED']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be ACTIVE, INACTIVE, or ARCHIVED"
            )

        success = update_exam_status(db, exam_id, status_value)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found"
            )

        logger.info(
            "Updated exam status",
            exam_id=exam_id,
            new_status=status_value,
            admin=current_admin.admin_id
        )

        return SuccessResponse(
            success=True,
            message=f"Exam status updated to {status_value}",
            data={"exam_id": exam_id, "status": status_value}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating exam status", exam_id=exam_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exam status"
        )


@exam_router.delete("/{exam_id}", response_model=SuccessResponse)
async def delete_exam(
        exam_id: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Delete an exam and all related data (USE WITH CAUTION)
    """
    try:
        success = delete_exam_by_id(db, exam_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found"
            )

        logger.warning(
            "Exam deleted",
            exam_id=exam_id,
            admin=current_admin.admin_id,
            action="DELETE_EXAM"
        )

        return SuccessResponse(
            success=True,
            message="Exam deleted successfully",
            data={"exam_id": exam_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting exam", exam_id=exam_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete exam"
        )


async def create_exam_folder_structure(exam_id: str, subject_codes: List[str]):
    """
    Background task to create folder structure for exam
    """
    try:
        from ..crud.exam import create_exam_folders
        create_exam_folders(exam_id, subject_codes)

        logger.info(
            "Exam folder structure created",
            exam_id=exam_id,
            subjects=subject_codes
        )

    except Exception as e:
        logger.error(
            "Failed to create exam folder structure",
            exam_id=exam_id,
            error=str(e)
        )
