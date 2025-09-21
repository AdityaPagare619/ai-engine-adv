# ai_engine/src/knowledge_tracing/routes/pacing_route.py
from fastapi import APIRouter, HTTPException
from ..pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
import logging

router = APIRouter()
logger = logging.getLogger("pacing_route")

@router.post("/pacing/allocate-time")
async def allocate_time(request: TimeAllocationRequest):
    allocator = DynamicTimeAllocator()
    try:
        response = allocator.allocate(request)
        return response
    except Exception as e:
        logger.error(f"Error in /allocate-time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
