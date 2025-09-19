from fastapi import APIRouter, HTTPException
from ..bkt.service import update_knowledge_state
from ..bkt.schemas import TraceRequest, TraceResponse

router = APIRouter()

@router.post("/ai/trace/update", response_model=TraceResponse)
async def trace_update(req: TraceRequest):
    try:
        return await update_knowledge_state(req)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: BKT update failed")
