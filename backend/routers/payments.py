"""
DocSetu AI - Payments Router
Handles subscription plans, Razorpay order creation, payment verification, and webhooks.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import get_settings
from db import get_db
from models.database import User
from routers.auth import get_current_user
from services.payment_service import (
    PLANS,
    create_order,
    get_plan_by_id,
    get_subscription_status,
    handle_webhook_event,
    verify_payment,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# --- Request/Response Models ---


class CreateOrderRequest(BaseModel):
    """Request to create a Razorpay order."""
    plan_id: str
    currency: str = "INR"


class VerifyPaymentRequest(BaseModel):
    """Request to verify a Razorpay payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PlanResponse(BaseModel):
    """Plan details response."""
    id: str
    name: str
    price: int
    docs_per_month: int
    features: list


class OrderResponse(BaseModel):
    """Order creation response."""
    order_id: str
    amount: int
    currency: str
    plan_id: str
    subscription_id: str
    key_id: str


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response."""
    plan_id: str
    plan_name: str
    status: str
    docs_per_month: int
    features: list
    subscription_id: Optional[str] = None
    started_at: Optional[str] = None
    expires_at: Optional[str] = None


# --- Endpoints ---


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    """
    List all available subscription plans.

    Returns:
        List of available plans with pricing and features.
    """
    return PLANS


@router.post("/create-order", response_model=OrderResponse)
async def create_payment_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a Razorpay order for a subscription plan.

    Args:
        request: Plan ID and currency.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Order details including Razorpay order ID and key for frontend checkout.
    """
    # Validate plan
    plan = get_plan_by_id(request.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan_id: {request.plan_id}",
        )

    if plan["price"] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an order for a free or enterprise plan. Contact sales for enterprise.",
        )

    try:
        order = create_order(
            amount_paise=plan["price"],
            currency=request.currency,
            plan_id=request.plan_id,
            user_id=current_user.id,
            db=db,
        )
        return order
    except ValueError as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error creating order: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment order. Please try again.",
        )


@router.post("/verify")
async def verify_payment_endpoint(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify Razorpay payment signature after frontend checkout completion.

    Args:
        request: Razorpay order ID, payment ID, and signature.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Subscription activation details.
    """
    try:
        result = verify_payment(
            order_id=request.razorpay_order_id,
            payment_id=request.razorpay_payment_id,
            signature=request.razorpay_signature,
            db=db,
        )
        return {
            "success": True,
            "message": "Payment verified successfully",
            **result,
        }
    except ValueError as e:
        logger.warning(f"Payment verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying payment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment verification failed. Please contact support.",
        )


@router.get("/subscription", response_model=SubscriptionStatusResponse)
async def get_user_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the current user's subscription status.

    Args:
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Current subscription plan details and status.
    """
    return get_subscription_status(user_id=current_user.id, db=db)


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Razorpay webhook handler. Called by Razorpay on payment events.

    This endpoint does NOT require JWT authentication.
    It verifies the webhook signature using the Razorpay webhook secret.

    Handled events:
        - payment.captured
        - payment.failed
        - subscription.activated
        - subscription.cancelled
    """
    # Read raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify webhook signature
    if not verify_webhook_signature(body, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = payload.get("event", "")
    logger.info(f"Received Razorpay webhook: {event_type}")

    # Process event
    result = handle_webhook_event(event_type=event_type, payload=payload, db=db)

    return {"status": "ok", **result}
