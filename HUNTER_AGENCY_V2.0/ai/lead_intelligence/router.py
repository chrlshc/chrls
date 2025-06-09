from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_info():
    """Simple GET endpoint for lead intelligence."""
    return {"module": "lead_intelligence", "status": "ok"}

@router.post("/")
async def post_info(payload: dict):
    """Simple POST endpoint echoing payload."""
    return {"module": "lead_intelligence", "received": payload}
