# ai_engine/src/knowledge_tracing/routes/pacing_route.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import logging

from ..pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest

router = APIRouter()
logger = logging.getLogger("pacing_route")

@router.post("/ai/trace/pacing/allocate-time")
async def allocate_time(request: TimeAllocationRequest):
    """
    Allocate adaptive time for question based on real-time load and stress.
    """
    allocator = DynamicTimeAllocator()
    try:
        response = allocator.allocate(request)
        return response
    except Exception as e:
        logger.error(f"Error in /allocate-time endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
