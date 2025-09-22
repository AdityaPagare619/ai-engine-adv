# Time Context Service - Standalone FastAPI Service
# Integrates with AI Engine for complete time intelligence

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional, Any
import logging
import asyncpg
import os
import json
from datetime import datetime, date, timedelta
import sys

# Add path for imports
sys.path.append('/app')

# Import time context processor
from ai_engine.src.time_context_processor import TimeContextProcessor, ExamPhase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="JEE Time Context Service",
    description="Exam countdown and time-aware preparation intelligence",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
time_processor = None
db_pool = None

# Pydantic models
class ExamScheduleRequest(BaseModel):
    exam_id: str
    student_id: Optional[str] = None
    target_exam_date: date
    preparation_start_date: Optional[date] = None
    
    @validator('preparation_start_date')
    def validate_prep_date(cls, v, values):
        if v and 'target_exam_date' in values:
            if v >= values['target_exam_date']:
                raise ValueError('Preparation start date must be before exam date')
        return v

class TimeContextResponse(BaseModel):
    student_id: str
    exam_id: str
    days_remaining: int
    current_phase: str
    urgency_level: str
    daily_study_hours: float
    recommended_focus: List[str]
    weekly_targets: Dict[str, int]
    strategic_recommendations: Dict[str, Any]

class ExamScheduleResponse(BaseModel):
    schedule_id: str
    exam_id: str
    student_id: Optional[str]
    target_exam_date: date
    preparation_start_date: date
    phase_configs: Dict[str, Any]

# Database connection
async def get_db_connection():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "jee_smart_platform"),
            user=os.getenv("DB_USER", "jee_admin"),
            password=os.getenv("DB_PASSWORD", "secure_jee_2025"),
            min_size=5,
            max_size=15
        )
    return db_pool

# Service initialization
@app.on_event("startup")
async def startup_event():
    global time_processor
    
    logger.info("Starting Time Context Service...")
    
    # Initialize time processor
    time_processor = TimeContextProcessor()
    logger.info("Time Context Processor initialized")
    
    # Initialize database connection
    await get_db_connection()
    logger.info("Database connection established")
    
    logger.info("Time Context Service startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    
    if db_pool:
        await db_pool.close()
    
    logger.info("Time Context Service shutdown complete")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = await get_db_connection()
        async with db.acquire() as conn:
            await conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "time-context",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# =============================================================================
# EXAM SCHEDULE MANAGEMENT
# =============================================================================

@app.post("/schedules", response_model=ExamScheduleResponse)
async def create_exam_schedule(request: ExamScheduleRequest):
    """Create a new exam schedule"""
    try:
        db = await get_db_connection()
        
        # Set default preparation start date if not provided
        prep_start = request.preparation_start_date
        if not prep_start:
            # Default to 120 days before exam
            prep_start = request.target_exam_date - timedelta(days=120)
        
        # Generate phase configurations
        phase_configs = {
            "foundation_phase_days": 90,
            "building_phase_days": 60,
            "mastery_phase_days": 30,
            "confidence_phase_days": 30,
            "daily_study_hours": 6.0,
            "created_by": "time-context-service"
        }
        
        async with db.acquire() as conn:
            schedule_id = await conn.fetchval("""
                INSERT INTO exam_schedules 
                (exam_id, student_id, target_exam_date, preparation_start_date, phase_configs)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """,
                request.exam_id,
                request.student_id,
                request.target_exam_date,
                prep_start,
                json.dumps(phase_configs)
            )
        
        return ExamScheduleResponse(
            schedule_id=str(schedule_id),
            exam_id=request.exam_id,
            student_id=request.student_id,
            target_exam_date=request.target_exam_date,
            preparation_start_date=prep_start,
            phase_configs=phase_configs
        )
        
    except Exception as e:
        logger.error(f"Error creating exam schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedules/{exam_id}")
async def get_exam_schedules(exam_id: str, student_id: Optional[str] = None):
    """Get exam schedules"""
    try:
        db = await get_db_connection()
        
        async with db.acquire() as conn:
            if student_id:
                query = """
                    SELECT id, exam_id, student_id, target_exam_date, 
                           preparation_start_date, phase_configs
                    FROM exam_schedules
                    WHERE exam_id = $1 AND student_id = $2 AND status = 'ACTIVE'
                """
                rows = await conn.fetch(query, exam_id, student_id)
            else:
                query = """
                    SELECT id, exam_id, student_id, target_exam_date,
                           preparation_start_date, phase_configs
                    FROM exam_schedules
                    WHERE exam_id = $1 AND status = 'ACTIVE'
                """
                rows = await conn.fetch(query, exam_id)
        
        schedules = []
        for row in rows:
            schedules.append({
                "schedule_id": str(row['id']),
                "exam_id": row['exam_id'],
                "student_id": row['student_id'],
                "target_exam_date": row['target_exam_date'].isoformat(),
                "preparation_start_date": row['preparation_start_date'].isoformat(),
                "phase_configs": row['phase_configs']
            })
        
        return {"schedules": schedules, "count": len(schedules)}
        
    except Exception as e:
        logger.error(f"Error getting exam schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# TIME CONTEXT ANALYSIS
# =============================================================================

@app.get("/context/{exam_id}/{student_id}")
async def get_time_context(exam_id: str, student_id: str):
    """Get current time context for student and exam"""
    try:
        db = await get_db_connection()
        
        # Get exam schedule
        async with db.acquire() as conn:
            schedule = await conn.fetchrow("""
                SELECT target_exam_date, preparation_start_date, phase_configs
                FROM exam_schedules
                WHERE exam_id = $1 AND (student_id = $2 OR student_id IS NULL)
                AND status = 'ACTIVE'
                ORDER BY student_id DESC NULLS LAST
                LIMIT 1
            """, exam_id, student_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Exam schedule not found")
        
        # Get time context
        exam_datetime = datetime.combine(schedule['target_exam_date'], datetime.min.time())
        time_context = time_processor.get_time_context(exam_datetime)
        
        # Log context to database
        await log_time_context(student_id, exam_id, time_context)
        
        return {
            "student_id": student_id,
            "exam_id": exam_id,
            "target_exam_date": schedule['target_exam_date'].isoformat(),
            "days_remaining": time_context.days_remaining,
            "current_phase": time_context.phase.value,
            "urgency_level": time_context.urgency_level,
            "daily_study_hours": time_context.daily_study_hours,
            "recommended_focus": time_context.recommended_focus,
            "weekly_targets": time_context.weekly_targets,
            "phase_configs": schedule['phase_configs']
        }
        
    except Exception as e:
        logger.error(f"Error getting time context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/context/analysis")
async def get_strategic_analysis(request: dict):
    """Get strategic analysis with mastery data integration"""
    try:
        student_id = request.get('student_id')
        exam_id = request.get('exam_id')
        mastery_profile = request.get('mastery_profile', {})
        
        if not student_id or not exam_id:
            raise HTTPException(status_code=400, detail="student_id and exam_id required")
        
        # Get time context first
        context_response = await get_time_context(exam_id, student_id)
        
        # Create time context object
        exam_date = datetime.fromisoformat(context_response['target_exam_date'])
        time_context = time_processor.get_time_context(exam_date)
        
        # Generate strategic recommendations
        if mastery_profile:
            recommendations = time_processor.get_strategic_recommendations(
                time_context, mastery_profile
            )
        else:
            recommendations = {
                "message": "No mastery profile provided - general recommendations only",
                "immediate_actions": time_processor._get_immediate_actions(time_context, []),
                "study_plan": time_processor._generate_study_plan(time_context, [], [])
            }
        
        return {
            "student_id": student_id,
            "exam_id": exam_id,
            "time_context": {
                "days_remaining": time_context.days_remaining,
                "phase": time_context.phase.value,
                "urgency_level": time_context.urgency_level,
                "daily_study_hours": time_context.daily_study_hours
            },
            "strategic_recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in strategic analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/phases")
async def get_phase_information():
    """Get information about all preparation phases"""
    return {
        "phases": [
            {
                "name": "foundation",
                "description": "Building fundamental concepts and understanding",
                "typical_duration_days": 90,
                "daily_hours": 6.0,
                "focus": ["concept_building", "foundation_strengthening"],
                "mastery_threshold": 0.4
            },
            {
                "name": "building", 
                "description": "Developing problem-solving skills and application",
                "typical_duration_days": 60,
                "daily_hours": 7.0,
                "focus": ["skill_development", "problem_solving"],
                "mastery_threshold": 0.6
            },
            {
                "name": "mastery",
                "description": "Advanced problem solving and speed building",
                "typical_duration_days": 30,
                "daily_hours": 8.0,
                "focus": ["advanced_problems", "speed_building"],
                "mastery_threshold": 0.8
            },
            {
                "name": "confidence",
                "description": "Final revision and exam confidence building",
                "typical_duration_days": 30,
                "daily_hours": 8.0,
                "focus": ["revision", "mock_tests", "confidence_building"],
                "mastery_threshold": 0.9
            }
        ]
    }

# =============================================================================
# ANALYTICS AND REPORTING
# =============================================================================

@app.get("/analytics/phase-distribution")
async def get_phase_distribution():
    """Get distribution of students across phases"""
    try:
        db = await get_db_connection()
        
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT current_phase, urgency_level, COUNT(*) as student_count
                FROM time_context_logs
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY current_phase, urgency_level
                ORDER BY current_phase, urgency_level
            """)
        
        distribution = []
        for row in rows:
            distribution.append({
                "phase": row['current_phase'],
                "urgency_level": row['urgency_level'],
                "student_count": row['student_count']
            })
        
        return {"phase_distribution": distribution}
        
    except Exception as e:
        logger.error(f"Error getting phase distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/urgency-trends")
async def get_urgency_trends(days: int = 30):
    """Get urgency level trends over time"""
    try:
        db = await get_db_connection()
        
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    DATE(created_at) as date,
                    urgency_level,
                    COUNT(*) as count
                FROM time_context_logs
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(created_at), urgency_level
                ORDER BY date DESC, urgency_level
            """, days)
        
        trends = []
        for row in rows:
            trends.append({
                "date": row['date'].isoformat(),
                "urgency_level": row['urgency_level'],
                "count": row['count']
            })
        
        return {"urgency_trends": trends, "period_days": days}
        
    except Exception as e:
        logger.error(f"Error getting urgency trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def log_time_context(student_id: str, exam_id: str, time_context):
    """Log time context to database"""
    try:
        db = await get_db_connection()
        
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO time_context_logs 
                (student_id, exam_id, days_remaining, current_phase, urgency_level,
                 focus_recommendations, daily_targets)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                student_id,
                exam_id,
                time_context.days_remaining,
                time_context.phase.value,
                time_context.urgency_level,
                time_context.recommended_focus,
                json.dumps(time_context.weekly_targets)
            )
        
    except Exception as e:
        logger.error(f"Error logging time context: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)