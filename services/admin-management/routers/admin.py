"""
Admin Authentication Router
Handles admin login, token management, and admin operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import get_db
from config.logging import logger
from ..schemas.admin import AdminLogin, TokenResponse, AdminResponse
from ..security.auth import create_admin_token, get_current_admin

admin_router = APIRouter()


@admin_router.post("/login", response_model=TokenResponse)
async def admin_login(
        login_data: AdminLogin,
        db: Session = Depends(get_db)
):
    """
    Admin login endpoint
    Validates admin key and returns JWT token
    """
    try:
        # Create and return token
        token_response = create_admin_token(login_data.admin_key)

        logger.info(
            "Admin login successful",
            admin_id=token_response.admin_id
        )

        return token_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Admin login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@admin_router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Get current admin information
    """
    return current_admin


@admin_router.post("/logout")
async def admin_logout(
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Admin logout endpoint
    """
    logger.info("Admin logout", admin_id=current_admin.admin_id)

    return {
        "success": True,
        "message": "Logged out successfully"
    }


@admin_router.get("/verify-token")
async def verify_token(
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Verify token validity
    """
    return {
        "valid": True,
        "admin_id": current_admin.admin_id,
        "username": current_admin.username
    }
