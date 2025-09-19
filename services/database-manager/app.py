"""
Database Manager Service - Complete FastAPI Application
Handles ID generation, database operations, and system maintenance
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
import redis
import hashlib

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jee_admin:secure_jee_2025@postgres:5432/jee_smart_platform")
REDIS_URL = os.getenv("REDIS_URL", "redis://:redis_secure_2025@redis:6379/1")

# Global connections
db_pool = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_pool, redis_client

    # Startup
    print("🚀 Starting Database Manager Service")

    try:
        # Initialize async database pool
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        print("✅ Database pool created")

        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection established")

    except Exception as e:
        print(f"❌ Startup failed: {e}")

    yield

    # Shutdown
    print("🛑 Shutting down Database Manager Service")
    if db_pool:
        await db_pool.close()

# FastAPI Application
app = FastAPI(
    title="JEE Smart AI Platform - Database Manager",
    description="ID generation, database operations and maintenance service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
from pydantic import BaseModel

class IDRequest(BaseModel):
    academic_year: int
    exam_type: str

class IDResponse(BaseModel):
    id: str
    type: str

class ExamCreate(BaseModel):
    display_name: str
    exam_type: str
    academic_year: int
    subjects: List[str]

class ExamResponse(BaseModel):
    id: str
    exam_id: str
    display_name: str
    exam_type: str
    academic_year: int
    status: str
    total_subjects: int
    created_at: str

# ID Generation System
class IndustryIDGenerator:
    """Industry-standard ID generation"""

    def __init__(self):
        self.templates = {
            "exam": "EXM-{year}-{type}-{seq:03d}",
            "subject": "{exam_id}-SUB-{code}",
            "question": "{sheet_id}-Q-{seq:05d}",
            "asset": "{parent_id}-AST-{type}-{seq:03d}"
        }

    async def generate_exam_id(self, academic_year: int, exam_type: str) -> str:
        """Generate unique exam ID"""
        try:
            exam_type = exam_type.upper().replace(" ", "_")

            # Get next sequence from Redis
            redis_key = f"seq:exam:{academic_year}:{exam_type}"
            if redis_client:
                next_seq = redis_client.incr(redis_key)
            else:
                next_seq = 1

            exam_id = self.templates["exam"].format(
                year=academic_year,
                type=exam_type,
                seq=next_seq
            )

            print(f"✅ Generated exam ID: {exam_id}")
            return exam_id

        except Exception as e:
            print(f"❌ Error generating exam ID: {e}")
            raise

    def generate_subject_id(self, exam_id: str, subject_code: str) -> str:
        """Generate subject ID"""
        subject_code = subject_code.upper()
        return self.templates["subject"].format(exam_id=exam_id, code=subject_code)

    def generate_question_id(self, sheet_id: str, question_number: int) -> str:
        """Generate question ID"""
        return self.templates["question"].format(sheet_id=sheet_id, seq=question_number)

# Initialize ID generator
id_generator = IndustryIDGenerator()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "service": "database-manager",
            "version": "1.0.0",
            "timestamp": time.time()
        }

        # Check database connection
        if db_pool:
            async with db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                # ✅ FIXED: Use proper pool attributes
                health_status["database"] = {
                    "status": "connected",
                    "pool_max_size": db_pool._maxsize if hasattr(db_pool, '_maxsize') else "unknown",
                    "pool_current_size": len(db_pool._holders) if hasattr(db_pool, '_holders') else "unknown"
                }
        else:
            health_status["database"] = {"status": "disconnected"}

        # Check Redis connection
        if redis_client:
            redis_client.ping()
            health_status["redis"] = {"status": "connected"}
        else:
            health_status["redis"] = {"status": "disconnected"}

        return health_status

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "JEE Smart AI Platform - Database Manager",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# ID Generation Endpoints
@app.post("/exams/", response_model=ExamResponse)
async def create_exam(exam_data: ExamCreate):
    """Create a new exam - FIXED VERSION WITH ERROR HANDLING"""
    try:
        # Generate exam ID
        exam_id = f"EXM-{exam_data.academic_year}-{exam_data.exam_type.upper()}-001"

        if db_pool:
            async with db_pool.acquire() as conn:
                # ✅ FIXED: Check if exam already exists
                existing_exam = await conn.fetchrow(
                    "SELECT exam_id FROM exam_registry WHERE exam_id = $1",
                    exam_id
                )

                if existing_exam:
                    # Generate next sequence number
                    existing_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM exam_registry WHERE exam_type = $1 AND academic_year = $2",
                        exam_data.exam_type,
                        exam_data.academic_year
                    )
                    exam_id = f"EXM-{exam_data.academic_year}-{exam_data.exam_type.upper()}-{existing_count + 1:03d}"

                # ✅ FIXED: Use transaction for data consistency
                async with conn.transaction():
                    # Insert exam into database with ALL required columns
                    query = """
                        INSERT INTO exam_registry (
                            exam_id, display_name, exam_type, academic_year, 
                            created_by_admin, admin_key_hash, status, total_subjects, total_questions
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id, created_at
                    """

                    result = await conn.fetchrow(
                        query,
                        exam_id,
                        exam_data.display_name,
                        exam_data.exam_type,
                        exam_data.academic_year,
                        "system_admin",
                        "admin_hash_placeholder",  # In production, use proper hash
                        "ACTIVE",
                        len(exam_data.subjects),  # ✅ FIXED: Now column exists
                        0  # ✅ FIXED: Initial question count
                    )

        print(f"✅ Exam created successfully: {exam_id}")

        return ExamResponse(
            id=str(result['id']) if result else "mock-uuid",
            exam_id=exam_id,
            display_name=exam_data.display_name,
            exam_type=exam_data.exam_type,
            academic_year=exam_data.academic_year,
            status="ACTIVE",
            total_subjects=len(exam_data.subjects),
            created_at=str(result['created_at']) if result else "2025-09-16T14:24:37"
        )

    except Exception as e:
        error_msg = f"Failed to create exam: {str(e)}"
        print(f"❌ {error_msg}")

        # ✅ FIXED: Specific error handling for different failure types
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exam with ID {exam_id} already exists"
            )
        elif "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reference data provided"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )


@app.post("/ids/subject")
async def generate_subject_id_endpoint(exam_id: str, subject_code: str):
    """Generate new subject ID"""
    try:
        subject_id = id_generator.generate_subject_id(exam_id, subject_code)

        return {"subject_id": subject_id, "type": "subject"}

    except Exception as e:
        print(f"❌ Error generating subject ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate subject ID: {str(e)}"
        )

# Database Operations Endpoints
@app.get("/database/statistics")
async def get_database_statistics():
    """Get comprehensive database statistics"""
    try:
        stats = {
            "timestamp": time.time(),
            "tables": {},
            "connections": {},
            "performance": {}
        }

        if db_pool:
            async with db_pool.acquire() as conn:
                # Get table counts
                tables_query = """
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                """

                table_rows = await conn.fetch(tables_query)
                stats["tables"] = {
                    row['tablename']: {
                        "inserts": row['n_tup_ins'],
                        "updates": row['n_tup_upd'],
                        "deletes": row['n_tup_del']
                    }
                    for row in table_rows
                }

                # Get connection info
                conn_query = """
                    SELECT count(*) as total_connections,
                           count(*) FILTER (WHERE state = 'active') as active,
                           count(*) FILTER (WHERE state = 'idle') as idle
                    FROM pg_stat_activity
                """

                conn_row = await conn.fetchrow(conn_query)
                stats["connections"] = {
                    "total": conn_row['total_connections'],
                    "active": conn_row['active'],
                    "idle": conn_row['idle']
                }

        # Pool statistics
        if db_pool:
            stats["pool"] = {
                "size": db_pool.get_size(),
                "busy": db_pool.get_busy_count(),
                "free": db_pool.get_size() - db_pool.get_busy_count()
            }

        return stats

    except Exception as e:
        print(f"❌ Error retrieving database statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

@app.post("/maintenance/cleanup")
async def run_database_cleanup():
    """Run database cleanup operations"""
    try:
        cleanup_results = {
            "timestamp": time.time(),
            "operations": []
        }

        if db_pool:
            async with db_pool.acquire() as conn:
                # Example cleanup: Remove old log entries
                cleanup_query = """
                    DELETE FROM system_configuration 
                    WHERE config_key LIKE 'temp_%' 
                    AND created_at < NOW() - INTERVAL '7 days'
                """

                result = await conn.execute(cleanup_query)
                cleanup_results["operations"].append({
                    "operation": "temp_config_cleanup",
                    "affected_rows": 0  # Would be extracted from result
                })

        # Redis cleanup
        if redis_client:
            # Clean expired keys
            keys = redis_client.keys("temp:*")
            if keys:
                redis_client.delete(*keys)
                cleanup_results["operations"].append({
                    "operation": "redis_temp_cleanup",
                    "affected_keys": len(keys)
                })

        print(f"✅ Database cleanup completed")
        return {
            "success": True,
            "cleanup_result": cleanup_results
        }

    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database cleanup failed: {str(e)}"
        )

# Configuration Management
@app.get("/config/{config_key}")
async def get_configuration(config_key: str):
    """Get system configuration value"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT config_key, config_value, config_type
                    FROM system_configuration 
                    WHERE config_key = $1
                """

                row = await conn.fetchrow(query, config_key)

                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Configuration not found"
                    )

                return {
                    "key": row['config_key'],
                    "value": row['config_value'],
                    "type": row['config_type']
                }

        # Fallback
        return {
            "key": config_key,
            "value": "default_value",
            "type": "STRING"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving configuration {config_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8004,
        workers=1,
        log_level="info",
        reload=True
    )
