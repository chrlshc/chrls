"""FastAPI router exposing basic billing endpoints."""

from fastapi import APIRouter, HTTPException

from .stripe import (
    init_stripe,
    create_customer,
    create_subscription,
    cancel_subscription,
    list_subscriptions,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.on_event("startup")
def setup_stripe() -> None:
    """Initialize Stripe when the application starts."""
    try:
        init_stripe()
    except Exception as exc:  # pragma: no cover - fails if key missing
        raise RuntimeError(f"Failed to initialize Stripe: {exc}") from exc


@router.post("/customers", status_code=201)
def api_create_customer(email: str):
    """Create a new Stripe customer."""
    try:
        return create_customer(email=email)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/subscriptions", status_code=201)
def api_create_subscription(customer_id: str, price_id: str):
    """Create a subscription for a customer."""
    try:
        return create_subscription(customer_id, price_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/subscriptions/{subscription_id}", status_code=204)
def api_cancel_subscription(subscription_id: str):
    """Cancel a subscription."""
    try:
        cancel_subscription(subscription_id)
        return {"status": "cancelled"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/customers/{customer_id}/subscriptions")
def api_list_subscriptions(customer_id: str):
    """List subscriptions for a customer."""
    try:
        return list_subscriptions(customer_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
