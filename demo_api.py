"""
Demo API for testing Phase 4A BKT Integration
Simple FastAPI server to test the enhanced BKT repository with question metadata.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add ai_engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_engine', 'src'))

try:
    from knowledge_tracing.bkt.repository import BKTRepository, QuestionMetadata
    from knowledge_tracing.bkt.tests.mock_supabase import MockSupabaseClient
except ImportError as e:
    print(f"Import error: {e}")
    print("Using absolute imports...")
    from ai_engine.src.knowledge_tracing.bkt.repository import BKTRepository, QuestionMetadata
    from ai_engine.src.knowledge_tracing.bkt.tests.mock_supabase import MockSupabaseClient

app = FastAPI(
    title="JEE Smart AI Platform - BKT Demo API",
    description="Demo API for testing Phase 4A BKT integration with question metadata",
    version="4A.1.0"
)

# Initialize with mock client for demo
repository = BKTRepository()
repository.client = MockSupabaseClient()

class UpdateKnowledgeRequest(BaseModel):
    student_id: str
    concept_id: str
    question_id: Optional[str] = None
    is_correct: bool
    response_time_ms: int = 1000
    difficulty_level: Optional[str] = None
    bloom_level: Optional[str] = None

class UpdateKnowledgeResponse(BaseModel):
    student_id: str
    concept_id: str
    question_id: Optional[str]
    previous_mastery: float
    new_mastery: float
    learning_occurred: bool
    parameters_used: dict
    question_context: Optional[dict] = None
    explanation: dict

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "BKT Demo API",
        "phase": "4A Week 1",
        "features": ["question_metadata_integration", "adaptive_calibration"]
    }

@app.get("/ai/metadata/{question_id}")
def get_question_metadata(question_id: str):
    """Get cached question metadata for a specific question."""
    metadata = repository.get_question_metadata(question_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Question metadata not found")
    
    return {
        "question_id": metadata.question_id,
        "difficulty_calibrated": metadata.difficulty_calibrated,
        "bloom_level": metadata.bloom_level,
        "estimated_time_seconds": metadata.estimated_time_seconds,
        "required_process_skills": metadata.required_process_skills
    }

@app.post("/ai/trace/update", response_model=UpdateKnowledgeResponse)
def update_knowledge_trace(request: UpdateKnowledgeRequest):
    """Update student's knowledge state using BKT with question context."""
    
    # Get current state
    current_state = repository.get_state(request.student_id, request.concept_id)
    previous_mastery = current_state.mastery_probability
    
    # Get question metadata if question_id provided
    question_metadata = None
    if request.question_id:
        question_metadata = repository.get_question_metadata(request.question_id)
    
    # Get contextual parameters (with question metadata if available)
    params = repository.get_parameters_with_context(request.concept_id, question_metadata)
    
    # Simple BKT update logic (this would normally be in a service layer)
    if request.is_correct:
        # Increase mastery based on learning rate
        new_mastery = previous_mastery + (1 - previous_mastery) * params.learn_rate
    else:
        # Decrease mastery based on slip/guess rates
        new_mastery = previous_mastery * (1 - params.slip_rate)
    
    # Clamp to valid range
    new_mastery = max(0.0, min(1.0, new_mastery))
    
    # Save new state
    repository.save_state(request.student_id, request.concept_id, new_mastery)
    
    # Log the update
    repository.log_update(
        student_id=request.student_id,
        concept_id=request.concept_id,
        prev=previous_mastery,
        new=new_mastery,
        correct=request.is_correct,
        response_time_ms=request.response_time_ms
    )
    
    # Determine if significant learning occurred
    learning_occurred = abs(new_mastery - previous_mastery) > 0.05
    
    # Build explanation
    explanation = {
        "parameters_adjusted": question_metadata is not None,
        "base_params": {
            "learn_rate": 0.3,
            "slip_rate": 0.1, 
            "guess_rate": 0.2
        },
        "used_params": {
            "learn_rate": params.learn_rate,
            "slip_rate": params.slip_rate,
            "guess_rate": params.guess_rate
        },
        "difficulty_adjustment": 0.0,
        "bloom_adjustment": 0.0
    }
    
    if question_metadata:
        explanation["difficulty_adjustment"] = (params.slip_rate - 0.1)
        if question_metadata.bloom_level in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]:
            bloom_adjustments = {"Remember": -0.05, "Understand": 0.0, "Apply": 0.02, 
                               "Analyze": 0.05, "Evaluate": 0.08, "Create": 0.1}
            explanation["bloom_adjustment"] = bloom_adjustments.get(question_metadata.bloom_level, 0.0)
    
    question_context = None
    if question_metadata:
        question_context = {
            "difficulty_calibrated": question_metadata.difficulty_calibrated,
            "bloom_level": question_metadata.bloom_level,
            "estimated_time_seconds": question_metadata.estimated_time_seconds,
            "required_process_skills": question_metadata.required_process_skills
        }
    
    return UpdateKnowledgeResponse(
        student_id=request.student_id,
        concept_id=request.concept_id,
        question_id=request.question_id,
        previous_mastery=previous_mastery,
        new_mastery=new_mastery,
        learning_occurred=learning_occurred,
        parameters_used={
            "learn_rate": params.learn_rate,
            "slip_rate": params.slip_rate,
            "guess_rate": params.guess_rate
        },
        question_context=question_context,
        explanation=explanation
    )

@app.get("/ai/state/{student_id}/{concept_id}")
def get_knowledge_state(student_id: str, concept_id: str):
    """Get current knowledge state for a student and concept."""
    state = repository.get_state(student_id, concept_id)
    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "mastery_probability": state.mastery_probability,
        "practice_count": state.practice_count
    }

@app.get("/ai/concepts/{concept_id}/parameters")
def get_concept_parameters(concept_id: str, question_id: Optional[str] = None):
    """Get BKT parameters for a concept, optionally with question context."""
    question_metadata = None
    if question_id:
        question_metadata = repository.get_question_metadata(question_id)
    
    params = repository.get_parameters_with_context(concept_id, question_metadata)
    
    response = {
        "concept_id": concept_id,
        "parameters": {
            "learn_rate": params.learn_rate,
            "slip_rate": params.slip_rate,
            "guess_rate": params.guess_rate
        },
        "context_applied": question_metadata is not None
    }
    
    if question_metadata:
        response["question_context"] = {
            "question_id": question_metadata.question_id,
            "difficulty_calibrated": question_metadata.difficulty_calibrated,
            "bloom_level": question_metadata.bloom_level
        }
    
    return response

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting BKT Demo API...")
    print("📊 Phase 4A Week 1: Enhanced BKT with Question Metadata Integration")
    print("🔗 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)