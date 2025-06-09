from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def pipeline_status():
    """Basic GET endpoint for smart pipeline."""
    return {"module": "smart_pipeline", "status": "ok"}

@router.post("/")
async def pipeline_action(payload: dict):
    """Basic POST endpoint echoing payload."""
    return {"module": "smart_pipeline", "received": payload}
