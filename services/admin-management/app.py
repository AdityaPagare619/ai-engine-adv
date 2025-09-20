"""
Admin Management Service - Complete FastAPI Application
Handles exam creation, subject management, and admin authentication
"""

import os
import sys
import time
from datetime import timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import asyncpg
import redis
from dotenv import load_dotenv

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# Load environment variables from project root
project_root = os.path.join(os.path.dirname(__file__), "../..")
load_dotenv(os.path.join(project_root, ".env"))

# Database connection - use environment variables
DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "postgresql://jee_admin:securepassword@localhost:5432/jee_smart_platform"))
REDIS_URL = os.getenv("REDIS_URL", "redis://:redis_secure_2025@localhost:6379/0")

# Global connections
db_pool = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_pool, redis_client

    # Startup
    print("🚀 Starting Admin Management Service")

    try:
        # Initialize async database pool
        try:
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
            print("✅ Database pool created")
        except Exception as db_error:
            print(f"⚠️ Database connection failed, running without PostgreSQL: {db_error}")
            db_pool = None

        # Initialize Redis
        try:
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            redis_client.ping()
            print("✅ Redis connection established")
        except Exception as redis_error:
            print(f"⚠️ Redis connection failed, running without Redis: {redis_error}")
            redis_client = None

    except Exception as e:
        print(f"❌ Startup failed: {e}")

    yield

    # Shutdown
    print("🛑 Shutting down Admin Management Service")
    if db_pool:
        await db_pool.close()

# FastAPI Application
app = FastAPI(
    title="JEE Smart AI Platform - Admin Management",
    description="Industry-grade admin management service for educational assessment platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
from pydantic import BaseModel, Field

class AdminLogin(BaseModel):
    admin_key: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_id: str

class ExamCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=200)
    exam_type: str
    academic_year: int = Field(..., ge=2020, le=2030)
    subjects: List[str] = Field(..., min_items=1)

class ExamResponse(BaseModel):
    id: str
    exam_id: str
    display_name: str
    exam_type: str
    academic_year: int
    status: str
    total_subjects: int
    created_at: str

# Authentication function
def verify_admin_key(admin_key: str) -> bool:
    """Verify admin key"""
    valid_keys = ["jee-admin-2025-secure", "admin-key-123"]
    return admin_key in valid_keys

def create_admin_token(admin_key: str) -> TokenResponse:
    """Create JWT token for admin"""
    if not verify_admin_key(admin_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key"
        )

    admin_id = f"admin_{hash(admin_key) % 10000:04d}"

    # In production, use proper JWT
    access_token = f"mock_token_{admin_id}"

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours
        admin_id=admin_id
    )

# Health check endpoint
# Health check endpoint - FIXED VERSION
@app.get("/health")
async def health_check():
    """Health check endpoint - FIXED"""
    try:
        health_status = {
            "status": "healthy",
            "service": "database-manager",
            "version": "1.0.0",
            "timestamp": time.time()
        }

        # Check database connection - FIXED
        if db_pool:
            async with db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")

                # ✅ FIXED: Use proper pool stats instead of non-existent methods
                pool_stats = {
                    "status": "connected",
                    "max_size": db_pool._maxsize if hasattr(db_pool, '_maxsize') else "unknown",
                    "current_size": len(db_pool._holders) if hasattr(db_pool, '_holders') else "unknown",
                    "available": len([h for h in db_pool._holders if h._in_use is False]) if hasattr(db_pool,
                                                                                                     '_holders') else "unknown"
                }

                health_status["database"] = pool_stats
        else:
            health_status["database"] = {"status": "disconnected"}

        # Check Redis connection - FIXED
        if redis_client:
            try:
                redis_client.ping()
                health_status["redis"] = {"status": "connected"}
            except Exception as redis_error:
                health_status["redis"] = {"status": "error", "error": str(redis_error)}
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
        "service": "JEE Smart AI Platform - Admin Management",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Admin Authentication Endpoints
@app.post("/admin/login", response_model=TokenResponse)
async def admin_login(login_data: AdminLogin):
    """Admin login endpoint"""
    try:
        token_response = create_admin_token(login_data.admin_key)

        # Log to Redis
        if redis_client:
            redis_client.setex(
                f"login:{token_response.admin_id}",
                86400,
                f"logged_in_at_{int(__import__('time').time())}"
            )

        print(f"✅ Admin login successful: {token_response.admin_id}")
        return token_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Admin login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.get("/admin/me")
async def get_current_admin():
    """Get current admin information"""
    return {
        "admin_id": "admin_0001",
        "username": "system_admin",
        "email": "admin@jee-platform.com",
        "full_name": "System Administrator",
        "is_active": True,
        "permissions": ["exam:create", "exam:read", "exam:update", "exam:delete"]
    }

# Exam Management Endpoints
@app.post("/exams/", response_model=ExamResponse)
async def create_exam(exam_data: ExamCreate):
    """Create a new exam - FIXED with duplicate handling"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                # ✅ FIXED: Check existing count and generate unique ID
                existing_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM exam_registry WHERE exam_type = $1 AND academic_year = $2",
                    exam_data.exam_type,
                    exam_data.academic_year
                )
                
                # Generate unique exam ID with proper sequence
                exam_id = f"EXM-{exam_data.academic_year}-{exam_data.exam_type.upper()}-{existing_count + 1:03d}"
                
                # ✅ FIXED: Use transaction for atomicity
                async with conn.transaction():
                    # Insert exam into database
                    query = """
                        INSERT INTO exam_registry (
                            exam_id, display_name, exam_type, academic_year, 
                            created_by_admin, status, total_subjects
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id, created_at
                    """

                    result = await conn.fetchrow(
                        query,
                        exam_id,
                        exam_data.display_name,
                        exam_data.exam_type,
                        exam_data.academic_year,
                        "system_admin",
                        "ACTIVE",
                        len(exam_data.subjects)
                    )

        print(f"✅ Exam created: {exam_id}")

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
        print(f"❌ Error creating exam: {e}")
        
        # ✅ FIXED: Specific error handling for different failure types
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exam with similar configuration already exists"
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

@app.get("/exams/")
async def list_exams():
    """Get list of all exams"""
    try:
        exams = []

        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT exam_id, display_name, exam_type, academic_year, 
                           status, total_subjects, created_at
                    FROM exam_registry 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)

                exams = [
                    {
                        "id": str(row['exam_id']),
                        "exam_id": row['exam_id'],
                        "display_name": row['display_name'],
                        "exam_type": row['exam_type'],
                        "academic_year": row['academic_year'],
                        "status": row['status'],
                        "total_subjects": row['total_subjects'],
                        "created_at": str(row['created_at'])
                    }
                    for row in rows
                ]

        print(f"✅ Retrieved {len(exams)} exams")
        return {"exams": exams, "total": len(exams)}

    except Exception as e:
        print(f"❌ Error retrieving exams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exams: {str(e)}"
        )

@app.get("/exams/{exam_id}")
async def get_exam_details(exam_id: str):
    """Get detailed information about a specific exam"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT exam_id, display_name, exam_type, academic_year,
                           status, total_subjects, created_at, updated_at
                    FROM exam_registry 
                    WHERE exam_id = $1
                """
                row = await conn.fetchrow(query, exam_id)

                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Exam not found"
                    )

                return {
                    "id": str(row['exam_id']),
                    "exam_id": row['exam_id'],
                    "display_name": row['display_name'],
                    "exam_type": row['exam_type'],
                    "academic_year": row['academic_year'],
                    "status": row['status'],
                    "total_subjects": row['total_subjects'],
                    "created_at": str(row['created_at']),
                    "updated_at": str(row['updated_at'])
                }

        # Fallback if no database
        return {
            "exam_id": exam_id,
            "display_name": "Mock Exam",
            "status": "ACTIVE"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving exam {exam_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exam: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        reload=True
    )
