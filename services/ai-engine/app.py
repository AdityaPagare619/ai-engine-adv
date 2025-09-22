# AI Engine Service - FastAPI Production Implementation
# Integrates BKT Engine + Cognitive Load Manager + Time Context

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional, Any
import logging
import asyncio
import asyncpg
import redis
import json
from datetime import datetime, date
import os
import sys

# Add the ai_engine path to Python path
sys.path.append('/app')

# Import your enhanced BKT engine and existing load manager
from ai_engine.src.bkt_engine.multi_concept_bkt import EnhancedMultiConceptBKT
from ai_engine.src.time_context_processor import TimeContextProcessor, ExamPhase
from ai_engine.src.knowledge_tracing.cognitive.load_manager import CognitiveLoadManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="JEE Smart AI Engine",
    description="Production AI Engine with BKT, Cognitive Load Management, and Time Context Intelligence",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
bkt_engine = None
time_processor = None
redis_client = None
db_pool = None

# Pydantic models for API
class StudentResponse(BaseModel):
    student_id: str
    concept_id: str
    question_id: Optional[str] = None
    is_correct: bool
    response_time_ms: int
    difficulty_level: Optional[float] = 1.0
    context_factors: Optional[Dict[str, Any]] = {}
    
    @validator('response_time_ms')
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('Response time must be positive')
        return v

class MasteryPredictionRequest(BaseModel):
    student_id: str
    concept_id: str
    question_difficulty: Optional[float] = 1.0

class TimeContextRequest(BaseModel):
    student_id: str
    exam_id: str
    exam_date: date

class BatchUpdateRequest(BaseModel):
    updates: List[StudentResponse]

class MasteryUpdateResponse(BaseModel):
    success: bool
    student_id: str
    concept_id: str
    previous_mastery: float
    new_mastery: float
    confidence_level: float
    cognitive_load: Dict[str, Any]
    recommendations: List[str]
    error: Optional[str] = None

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
            max_size=20
        )
    return db_pool

# Redis connection
async def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client

# Initialize services
@app.on_event("startup")
async def startup_event():
    global bkt_engine, time_processor
    
    logger.info("Starting AI Engine services...")
    
    # Initialize BKT engine
    bkt_engine = EnhancedMultiConceptBKT()
    logger.info("BKT Engine initialized")
    
    # Initialize time processor
    time_processor = TimeContextProcessor()
    logger.info("Time Context Processor initialized")
    
    # Initialize database connection
    await get_db_connection()
    logger.info("Database connection established")
    
    # Initialize Redis
    await get_redis_client()
    logger.info("Redis connection established")
    
    logger.info("AI Engine startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    global db_pool, redis_client
    
    if db_pool:
        await db_pool.close()
    
    if redis_client:
        await redis_client.close()
    
    logger.info("AI Engine shutdown complete")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = await get_db_connection()
        async with db.acquire() as conn:
            await conn.execute("SELECT 1")
        
        # Test Redis connection
        redis_conn = await get_redis_client()
        await redis_conn.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "bkt_engine": "operational",
                "time_processor": "operational", 
                "database": "connected",
                "redis": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# =============================================================================
# BKT ENGINE ENDPOINTS
# =============================================================================

@app.post("/bkt/update-mastery", response_model=MasteryUpdateResponse)
async def update_student_mastery(response: StudentResponse, background_tasks: BackgroundTasks):
    """Update student mastery based on response"""
    try:
        # Get question metadata (simplified for now)
        question_metadata = {
            'solution_steps': 3,
            'concepts_required': [response.concept_id],
            'prerequisites': [],
            'learning_value': 0.7,
            'schema_complexity': 0.4
        }
        
        # Update mastery using BKT engine
        result = bkt_engine.update_mastery(
            student_id=response.student_id,
            concept_id=response.concept_id,
            is_correct=response.is_correct,
            question_metadata=question_metadata,
            context_factors=response.context_factors,
            response_time_ms=response.response_time_ms
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        # Store interaction log in database (background task)
        background_tasks.add_task(
            log_interaction_to_db,
            response,
            result
        )
        
        return MasteryUpdateResponse(
            success=True,
            student_id=result['student_id'],
            concept_id=result['concept_id'],
            previous_mastery=result['previous_mastery'],
            new_mastery=result['new_mastery'],
            confidence_level=result['confidence_level'],
            cognitive_load=result['cognitive_load'],
            recommendations=result['cognitive_load']['recommendations']
        )
        
    except Exception as e:
        logger.error(f"Error updating mastery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bkt/batch-update")
async def batch_update_mastery(request: BatchUpdateRequest, background_tasks: BackgroundTasks):
    """Batch update multiple student responses"""
    try:
        results = []
        
        for response in request.updates:
            # Process each update
            question_metadata = {
                'solution_steps': 3,
                'concepts_required': [response.concept_id],
                'prerequisites': [],
                'learning_value': 0.7,
                'schema_complexity': 0.4
            }
            
            result = bkt_engine.update_mastery(
                student_id=response.student_id,
                concept_id=response.concept_id,
                is_correct=response.is_correct,
                question_metadata=question_metadata,
                context_factors=response.context_factors,
                response_time_ms=response.response_time_ms
            )
            
            results.append(result)
            
            # Log to database (background)
            background_tasks.add_task(log_interaction_to_db, response, result)
        
        return {
            "success": True,
            "processed_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bkt/predict-performance")
async def predict_performance(request: MasteryPredictionRequest = Depends()):
    """Predict student performance on a question"""
    try:
        prediction = bkt_engine.predict_performance(
            student_id=request.student_id,
            concept_id=request.concept_id,
            question_difficulty=request.question_difficulty
        )
        
        return prediction
        
    except Exception as e:
        logger.error(f"Error predicting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bkt/student-profile/{student_id}")
async def get_student_profile(student_id: str):
    """Get comprehensive student mastery profile"""
    try:
        profile = bkt_engine.get_student_profile(student_id)
        
        if 'error' in profile:
            raise HTTPException(status_code=404, detail=profile['error'])
        
        return profile
        
    except Exception as e:
        logger.error(f"Error getting student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bkt/performance-summary")
async def get_bkt_performance():
    """Get overall BKT engine performance summary"""
    try:
        summary = bkt_engine.get_performance_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# TIME CONTEXT ENDPOINTS  
# =============================================================================

@app.post("/time-context/analysis")
async def get_time_context_analysis(request: TimeContextRequest):
    """Get time context analysis and strategic recommendations"""
    try:
        # Convert date to datetime
        exam_datetime = datetime.combine(request.exam_date, datetime.min.time())
        
        # Get time context
        time_context = time_processor.get_time_context(exam_datetime)
        
        # Get student mastery profile from BKT
        student_profile = bkt_engine.get_student_profile(request.student_id)
        
        if 'error' not in student_profile:
            # Generate strategic recommendations
            recommendations = time_processor.get_strategic_recommendations(
                time_context, student_profile
            )
        else:
            recommendations = {"message": "No mastery data available for recommendations"}
        
        return {
            "student_id": request.student_id,
            "exam_id": request.exam_id,
            "time_context": {
                "days_remaining": time_context.days_remaining,
                "phase": time_context.phase.value,
                "urgency_level": time_context.urgency_level,
                "daily_study_hours": time_context.daily_study_hours,
                "recommended_focus": time_context.recommended_focus,
                "weekly_targets": time_context.weekly_targets
            },
            "strategic_recommendations": recommendations,
            "mastery_summary": student_profile if 'error' not in student_profile else None
        }
        
    except Exception as e:
        logger.error(f"Error in time context analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/time-context/phase/{days_remaining}")
async def get_exam_phase(days_remaining: int):
    """Get exam preparation phase for given days remaining"""
    try:
        # Create a mock exam date
        exam_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        exam_date = exam_date.replace(day=exam_date.day + days_remaining)
        
        time_context = time_processor.get_time_context(exam_date)
        
        return {
            "days_remaining": days_remaining,
            "phase": time_context.phase.value,
            "urgency_level": time_context.urgency_level,
            "recommended_focus": time_context.recommended_focus,
            "daily_study_hours": time_context.daily_study_hours
        }
        
    except Exception as e:
        logger.error(f"Error getting exam phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# INTEGRATED ENDPOINTS
# =============================================================================

@app.post("/integrated/student-intelligence")
async def get_integrated_student_intelligence(request: TimeContextRequest):
    """Get complete student intelligence: BKT + Time Context + Recommendations"""
    try:
        # Get BKT profile
        bkt_profile = bkt_engine.get_student_profile(request.student_id)
        
        # Get time context analysis  
        exam_datetime = datetime.combine(request.exam_date, datetime.min.time())
        time_analysis = time_processor.integrate_with_bkt(
            bkt_engine, request.student_id, exam_datetime
        )
        
        # Combine results
        return {
            "student_id": request.student_id,
            "exam_id": request.exam_id,
            "timestamp": datetime.now().isoformat(),
            "bkt_profile": bkt_profile,
            "time_intelligence": time_analysis,
            "ai_engine_health": bkt_engine.get_performance_summary()
        }
        
    except Exception as e:
        logger.error(f"Error in integrated intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def log_interaction_to_db(response: StudentResponse, bkt_result: Dict):
    """Log interaction to database"""
    try:
        db = await get_db_connection()
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO bkt_interaction_logs 
                (student_id, concept_id, question_id, is_correct, response_time_ms,
                 previous_mastery, new_mastery, cognitive_load_total, overload_risk,
                 interaction_context, bkt_parameters_used)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                response.student_id,
                response.concept_id,
                response.question_id,
                response.is_correct,
                response.response_time_ms,
                bkt_result.get('previous_mastery'),
                bkt_result.get('new_mastery'),
                bkt_result.get('cognitive_load', {}).get('total_load'),
                bkt_result.get('cognitive_load', {}).get('overload_risk'),
                json.dumps(response.context_factors),
                json.dumps({})  # BKT parameters used
            )
            
            # Also update mastery state
            await conn.execute("""
                INSERT INTO student_mastery_states 
                (student_id, concept_id, subject_id, mastery_probability, confidence_level, practice_count)
                VALUES ($1, $2, $3, $4, $5, 1)
                ON CONFLICT (student_id, concept_id, subject_id)
                DO UPDATE SET
                    mastery_probability = $4,
                    confidence_level = $5,
                    practice_count = student_mastery_states.practice_count + 1,
                    last_interaction = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """,
                response.student_id,
                response.concept_id,
                'PHY',  # Default subject for now
                bkt_result.get('new_mastery'),
                bkt_result.get('confidence_level')
            )
        
        logger.info(f"Logged interaction for {response.student_id}/{response.concept_id}")
        
    except Exception as e:
        logger.error(f"Error logging interaction to DB: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)