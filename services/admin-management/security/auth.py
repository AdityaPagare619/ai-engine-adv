"""
Authentication and Authorization Module
JWT-based admin authentication system
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from config.database import get_db
from config.security import security
from config.logging import logger
from ..models.admin import AdminUser
from ..schemas.admin import AdminResponse, TokenResponse

# Security scheme
security_scheme = HTTPBearer()


async def verify_admin_token(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        token = credentials.credentials
        payload = security.verify_access_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(
        token_payload: dict = Depends(verify_admin_token),
        db: Session = Depends(get_db)
) -> AdminResponse:
    """Get current authenticated admin user"""
    try:
        admin_id = token_payload.get("sub")
        if not admin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # For now, return a mock admin response since we're using admin_key auth
        # In production, you'd query the admin_users table
        admin = AdminResponse(
            id="admin-uuid",
            admin_id=admin_id,
            username="system_admin",
            email="admin@jee-platform.com",
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            last_login=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

        return admin

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting current admin", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve admin information"
        )


def create_admin_token(admin_key: str) -> TokenResponse:
    """Create JWT token for admin"""
    try:
        # Verify admin key
        if not security.verify_admin_key(admin_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin key"
            )

        # Create token payload
        admin_id = f"admin_{hash(admin_key) % 10000:04d}"
        token_data = {
            "sub": admin_id,
            "type": "admin",
            "permissions": ["exam:create", "exam:read", "exam:update", "exam:delete"]
        }

        # Generate token
        access_token = security.create_access_token(token_data)

        logger.info("Admin token created", admin_id=admin_id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=security.JWT_EXPIRATION_MINUTES * 60,
            admin_id=admin_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating admin token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create authentication token"
        )
