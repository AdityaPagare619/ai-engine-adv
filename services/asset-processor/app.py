"""
Asset Processor Service
Handles ingestion, processing, optimization, and delivery of images and diagrams linked to questions.
"""

import os
import sys
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg
import structlog
from typing import Optional
from fastapi.responses import FileResponse

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# from routers.assets import router as asset_router
from pydantic_settings import BaseSettings
from pydantic import Field

logger = structlog.get_logger()

class AssetProcessorSettings(BaseSettings):
    ALLOWED_IMAGE_FORMATS: list[str] = Field(default=["png", "jpeg", "jpg", "webp", "svg"])
    OPTIMIZATION_LEVEL: str = Field(default="STANDARD")
    UPLOAD_DIR: str = Field(default="uploads/assets")
    ENV_FILE: str = Field(default=".env")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

asset_settings = AssetProcessorSettings()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jee_admin:secure_jee_2025@postgres:5432/jee_smart_platform")

db_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> AsyncSession:
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return db_pool

app = FastAPI(title="Asset Processor Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    os.makedirs(asset_settings.UPLOAD_DIR, exist_ok=True)
    await get_db_pool()
    logger.info("Asset Processor Service started")

@app.get("/health")
async def health():
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "asset-processor", "version": app.version}
    except Exception as e:
        logger.error("Health check error", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Basic asset upload endpoint for testing
@app.post("/assets/upload")
async def upload_asset(question_id: str, file: UploadFile = File(...)):
    """Simple asset upload for Phase 2B testing"""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(400, "Only image files supported")
        
        # Generate asset ID
        asset_id = str(uuid.uuid4())
        filename = f"{asset_id}_{file.filename}"
        
        # Save file
        os.makedirs("uploads/assets", exist_ok=True)
        file_path = f"uploads/assets/{filename}"
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Insert into database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO question_assets (
                    asset_id, question_id, asset_type, asset_role,
                    original_filename, storage_path, mime_type, 
                    file_size_bytes, processing_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                asset_id, question_id, "IMAGE", "QUESTION_IMAGE",
                file.filename, file_path, file.content_type,
                len(contents), "COMPLETED"
            )
        
        logger.info("Asset uploaded", asset_id=asset_id, question_id=question_id)
        return {
            "asset_id": asset_id,
            "question_id": question_id,
            "filename": file.filename,
            "status": "uploaded"
        }
    except Exception as e:
        logger.error("Asset upload failed", error=str(e))
        raise HTTPException(500, f"Upload failed: {str(e)}")
