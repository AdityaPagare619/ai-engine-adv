#!/usr/bin/env python3
"""
Simple FastAPI service for integration testing
Minimal dependencies version for testing the BKT infrastructure
"""

import os
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# FastAPI Application
app = FastAPI(
    title="JEE Smart AI Platform - Test Service",
    description="Minimal service for BKT integration testing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: float

class BKTUpdateRequest(BaseModel):
    student_id: str
    concept_id: str
    is_correct: bool
    response_time_ms: int = 0

class BKTUpdateResponse(BaseModel):
    student_id: str
    concept_id: str
    previous_mastery: float
    new_mastery: float
    updated_at: float

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for infrastructure verification"""
    return HealthResponse(
        status="healthy",
        service="jee-smart-ai-test-service",
        version="1.0.0",
        timestamp=time.time()
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "JEE Smart AI Platform - Test Service",
        "version": "1.0.0", 
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Mock BKT endpoints for integration testing
@app.post("/api/v1/bkt/update", response_model=BKTUpdateResponse)
async def update_knowledge_state(request: BKTUpdateRequest):
    """Mock BKT update endpoint for integration testing"""
    # Simulate BKT calculation
    previous_mastery = 0.5  # Default starting mastery
    
    # Simple mock calculation
    if request.is_correct:
        new_mastery = min(0.95, previous_mastery + 0.1)
    else:
        new_mastery = max(0.05, previous_mastery - 0.05)
    
    return BKTUpdateResponse(
        student_id=request.student_id,
        concept_id=request.concept_id,
        previous_mastery=previous_mastery,
        new_mastery=new_mastery,
        updated_at=time.time()
    )

@app.get("/api/v1/bkt/state/{student_id}/{concept_id}")
async def get_knowledge_state(student_id: str, concept_id: str):
    """Get current knowledge state for student and concept"""
    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "mastery_probability": 0.65,  # Mock value
        "practice_count": 5,
        "last_updated": time.time()
    }

@app.get("/api/v1/bkt/parameters/{concept_id}")
async def get_bkt_parameters(concept_id: str):
    """Get BKT parameters for a concept"""
    # Mock parameters based on concept
    params_map = {
        "kinematics_basic": {"learn_rate": 0.25, "slip_rate": 0.10, "guess_rate": 0.20},
        "thermodynamics_basic": {"learn_rate": 0.22, "slip_rate": 0.12, "guess_rate": 0.18},
        "organic_chemistry_basic": {"learn_rate": 0.28, "slip_rate": 0.08, "guess_rate": 0.22},
        "calculus_derivatives": {"learn_rate": 0.30, "slip_rate": 0.09, "guess_rate": 0.15},
        "algebra_quadratics": {"learn_rate": 0.35, "slip_rate": 0.07, "guess_rate": 0.18},
    }
    
    params = params_map.get(concept_id, {"learn_rate": 0.3, "slip_rate": 0.1, "guess_rate": 0.2})
    
    return {
        "concept_id": concept_id,
        **params,
        "created_at": time.time(),
        "updated_at": time.time()
    }

@app.get("/api/v1/questions/{question_id}")
async def get_question_metadata(question_id: str):
    """Get question metadata"""
    # Mock question data
    questions = {
        "PHY_MECH_0001": {
            "question_id": "PHY_MECH_0001",
            "subject": "Physics",
            "topic": "Kinematics", 
            "difficulty_calibrated": 1.2,
            "bloom_level": "Apply",
            "estimated_time_seconds": 120,
            "required_process_skills": ["kinematics", "problem_solving"]
        },
        "CHEM_ORG_0001": {
            "question_id": "CHEM_ORG_0001",
            "subject": "Chemistry",
            "topic": "Organic Chemistry",
            "difficulty_calibrated": 0.8,
            "bloom_level": "Understand", 
            "estimated_time_seconds": 90,
            "required_process_skills": ["organic_reactions", "nomenclature"]
        },
        "MATH_CALC_0001": {
            "question_id": "MATH_CALC_0001",
            "subject": "Mathematics",
            "topic": "Calculus",
            "difficulty_calibrated": 1.5,
            "bloom_level": "Apply",
            "estimated_time_seconds": 150,
            "required_process_skills": ["differentiation", "problem_solving"]
        }
    }
    
    question_data = questions.get(question_id)
    if not question_data:
        raise HTTPException(status_code=404, detail="Question not found")
        
    return question_data

# Mock admin endpoints
@app.post("/admin/login")
async def admin_login():
    """Mock admin login"""
    return {
        "access_token": "mock_admin_token_12345",
        "token_type": "bearer",
        "expires_in": 86400
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting JEE Smart AI Test Service on port 8000...")
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )