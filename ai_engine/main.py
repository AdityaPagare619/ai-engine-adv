# ai_engine/main.py
from fastapi import FastAPI
from src.knowledge_tracing.routes.pacing_route import router as pacing_router
from src.admin.exam_config_route import router as exam_admin_router

app = FastAPI(title="Smart AI Engine - Phase 4B")

@app.get("/")
async def root():
    return {"message": "Phase 4B AI Engine Running", "status": "healthy"}

@app.get("/health")
async def health_check():
    from src.config.exam_config import EXAM_CONFIGS
    return {
        "status": "healthy",
        "version": "Phase 4B",
        "exam_configs": list(EXAM_CONFIGS.keys())
    }

# Routes
app.include_router(pacing_router, prefix="/ai/trace", tags=["pacing"])
app.include_router(exam_admin_router, tags=["admin"])
