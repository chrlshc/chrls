from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def billing_status():
    """Basic GET endpoint for billing."""
    return {"module": "billing", "status": "ok"}

@router.post("/")
async def billing_action(payload: dict):
    """Basic POST endpoint echoing payload."""
    return {"module": "billing", "received": payload}
