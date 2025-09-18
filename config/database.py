"""
Database Configuration Module
Handles all database connections, pooling, and settings
"""

import os
from typing import Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import redis
import asyncpg


# Database Configuration
class DatabaseConfig:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL",
                                      "postgresql://jee_admin:secure_password@localhost:5432/jee_smart_platform")
        self.DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
        self.DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
        self.DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        self.DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

        # Redis Configuration
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return self.DATABASE_URL

    def get_redis_config(self) -> dict:
        """Get Redis configuration"""
        return {
            "url": self.REDIS_URL,
            "password": self.REDIS_PASSWORD,
            "decode_responses": True,
            "health_check_interval": 30
        }


# SQLAlchemy Setup
db_config = DatabaseConfig()

engine = create_engine(
    db_config.get_database_url(),
    poolclass=QueuePool,
    pool_size=db_config.DATABASE_POOL_SIZE,
    max_overflow=db_config.DATABASE_MAX_OVERFLOW,
    pool_timeout=db_config.DATABASE_POOL_TIMEOUT,
    pool_recycle=db_config.DATABASE_POOL_RECYCLE,
    echo=False,  # Set to True for SQL debugging
    future=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# AsyncPG Connection Pool (for high-performance operations)
async_pool: Optional[asyncpg.Pool] = None


async def create_async_pool():
    """Create async connection pool"""
    global async_pool
    if not async_pool:
        async_pool = await asyncpg.create_pool(
            db_config.get_database_url().replace("postgresql://", "postgresql://"),
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    return async_pool


async def get_async_connection():
    """Get async database connection"""
    pool = await create_async_pool()
    async with pool.acquire() as connection:
        yield connection


# Redis Connection
redis_client = None


def get_redis_client():
    """Get Redis client"""
    global redis_client
    if not redis_client:
        redis_config = db_config.get_redis_config()
        redis_client = redis.from_url(
            redis_config["url"],
            password=redis_config["password"],
            decode_responses=redis_config["decode_responses"],
            health_check_interval=redis_config["health_check_interval"]
        )
    return redis_client


# Database Dependency
def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Metadata for migrations
metadata = MetaData()
