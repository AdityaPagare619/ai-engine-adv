# test_main.py - Simplified version for testing
import sys
import os

# Add current directory to Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from src.knowledge_tracing.routes.pacing_route import router as pacing_router
from src.config.exam_config import EXAM_CONFIGS

app = FastAPI(title="Smart AI Engine - Phase 4B Testing")

# Add basic health check
@app.get("/")
async def root():
    return {"message": "Phase 4B AI Engine Running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "Phase 4B",
        "exam_configs": list(EXAM_CONFIGS.keys())
    }

# Include pacing router for time allocation testing
app.include_router(pacing_router, prefix="/ai/trace", tags=["pacing"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)