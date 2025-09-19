"""
Environment Configuration Module
Centralized environment variable management
"""

import os
from enum import Enum
from typing import List, Optional
from pydantic import BaseSettings, Field


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT)
    DEBUG: bool = Field(default=True)

    # Application
    APP_NAME: str = Field(default="JEE Smart AI Platform")
    APP_VERSION: str = Field(default="1.0.0")
    API_V1_PREFIX: str = Field(default="/api/v1")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=1)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://jee_admin:secure_password@localhost:5432/jee_smart_platform"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=30)

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # Security
    JWT_SECRET_KEY: str = Field(default="your-super-secret-jwt-key-change-this-immediately")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=1440)
    ADMIN_KEY_HASH: str = Field(default="$2b$12$LQv3c1yqBWVHxkd0LQ1NGO.NxBYNGkVLNzYK0hGN4z6fwF2qV2tWy")

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=52428800)  # 50MB
    ALLOWED_EXTENSIONS: List[str] = Field(default=["csv", "xlsx", "png", "jpg", "jpeg", "webp", "svg"])
    UPLOAD_DIRECTORY: str = Field(default="data/uploads")

    # Asset Processing
    ASSET_OPTIMIZATION_LEVEL: str = Field(default="STANDARD")
    WEBP_QUALITY: int = Field(default=85)
    PNG_OPTIMIZATION: bool = Field(default=True)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: str = Field(default="logs/app.log")

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"])

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=3600)

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)
    HEALTH_CHECK_INTERVAL: int = Field(default=30)

    # Backup
    BACKUP_RETENTION_DAYS: int = Field(default=30)
    BACKUP_DIRECTORY: str = Field(default="backups")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Environment-specific configurations
def get_database_url() -> str:
    """Get environment-specific database URL"""
    if settings.ENVIRONMENT == Environment.TESTING:
        return settings.DATABASE_URL.replace("/jee_smart_platform", "/jee_smart_platform_test")
    return settings.DATABASE_URL


def is_production() -> bool:
    """Check if running in production"""
    return settings.ENVIRONMENT == Environment.PRODUCTION


def is_development() -> bool:
    """Check if running in development"""
    return settings.ENVIRONMENT == Environment.DEVELOPMENT


def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    if is_production():
        return ["https://your-domain.com"]
    return settings.CORS_ORIGINS
