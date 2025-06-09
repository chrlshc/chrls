from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def social_status():
    """Basic GET endpoint for social automation."""
    return {"module": "social_automation", "status": "ok"}

@router.post("/")
async def social_action(payload: dict):
    """Basic POST endpoint echoing payload."""
    return {"module": "social_automation", "received": payload}
