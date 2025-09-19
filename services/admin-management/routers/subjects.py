"""
Subject Management Router
Handles subject-specific operations within exams
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import get_db
from config.logging import logger
from ..schemas.exam import SubjectResponse, SuccessResponse
from ..schemas.admin import AdminResponse
from ..security.auth import get_current_admin
from ..crud.exam import get_subjects_by_exam, get_subject_by_id, update_subject_status

subject_router = APIRouter()


@subject_router.get("/exam/{exam_id}", response_model=List[SubjectResponse])
async def get_exam_subjects(
        exam_id: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Get all subjects for a specific exam
    """
    try:
        subjects = get_subjects_by_exam(db, exam_id)

        logger.info(
            "Retrieved exam subjects",
            exam_id=exam_id,
            count=len(subjects),
            admin=current_admin.admin_id
        )

        return subjects

    except Exception as e:
        logger.error("Error retrieving exam subjects", exam_id=exam_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subjects"
        )


@subject_router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject_details(
        subject_id: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Get detailed information about a specific subject
    """
    try:
        subject = get_subject_by_id(db, subject_id)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )

        logger.info(
            "Retrieved subject details",
            subject_id=subject_id,
            admin=current_admin.admin_id
        )

        return subject

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving subject", subject_id=subject_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subject"
        )


@subject_router.put("/{subject_id}/status", response_model=SuccessResponse)
async def update_subject_status_endpoint(
        subject_id: str,
        status_value: str,
        db: Session = Depends(get_db),
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Update subject status (ACTIVE, INACTIVE)
    """
    try:
        if status_value not in ['ACTIVE', 'INACTIVE']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be ACTIVE or INACTIVE"
            )

        success = update_subject_status(db, subject_id, status_value)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )

        logger.info(
            "Updated subject status",
            subject_id=subject_id,
            new_status=status_value,
            admin=current_admin.admin_id
        )

        return SuccessResponse(
            success=True,
            message=f"Subject status updated to {status_value}",
            data={"subject_id": subject_id, "status": status_value}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating subject status", subject_id=subject_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subject status"
        )
