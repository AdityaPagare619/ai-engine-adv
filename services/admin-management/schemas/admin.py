"""
Admin Pydantic Schemas
Authentication and admin management schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AdminLogin(BaseModel):
    admin_key: str = Field(..., min_length=8, max_length=100)

    class Config:
        schema_extra = {
            "example": {
                "admin_key": "your-secure-admin-key"
            }
        }


class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: str = Field(..., min_length=1, max_length=200)
    admin_key: str = Field(..., min_length=8)

    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "username": "admin_user",
                "email": "admin@example.com",
                "full_name": "System Administrator",
                "admin_key": "your-secure-admin-key"
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_id: str

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "admin_id": "admin_001"
            }
        }


class AdminResponse(BaseModel):
    id: str
    admin_id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminListResponse(BaseModel):
    id: str
    admin_id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
