from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_status():
    """Basic GET endpoint for email engine."""
    return {"module": "email_engine", "status": "ok"}

@router.post("/")
async def post_status(payload: dict):
    """Basic POST endpoint echoing payload."""
    return {"module": "email_engine", "received": payload}
