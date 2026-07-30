"""
DocSetu AI - Payment Service
Razorpay payment gateway integration for subscription management.
"""

import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

import razorpay
from sqlalchemy.orm import Session

from config import get_settings
from models.database import Subscription, Payment

logger = logging.getLogger(__name__)
settings = get_settings()

# Subscription plans (prices in paise)
PLANS = [
    {
        "id": "free",
        "name": "Free",
        "price": 0,
        "docs_per_month": 10,
        "features": ["Basic OCR", "2 languages"],
    },
    {
        "id": "starter",
        "name": "Starter",
        "price": 299900,
        "docs_per_month": 500,
        "features": ["5 languages", "Compliance checks", "Email support"],
    },
    {
        "id": "business",
        "name": "Business",
        "price": 1499900,
        "docs_per_month": 5000,
        "features": [
            "All languages",
            "Compliance autopilot",
            "Priority support",
            "PDF export",
        ],
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "price": 0,
        "docs_per_month": -1,
        "features": ["Custom", "Dedicated AM", "SLA"],
    },
]


def _get_razorpay_client() -> razorpay.Client:
    """Initialize and return Razorpay client."""
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ValueError("Razorpay credentials not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def get_plan_by_id(plan_id: str) -> Optional[dict]:
    """Get a plan by its ID."""
    for plan in PLANS:
        if plan["id"] == plan_id:
            return plan
    return None


def create_order(amount_paise: int, currency: str, plan_id: str, user_id: str, db: Session) -> dict:
    """
    Create a Razorpay order for a subscription plan.

    Args:
        amount_paise: Amount in paise (e.g., 299900 for ₹2999).
        currency: Currency code (default INR).
        plan_id: The plan ID being purchased.
        user_id: The user making the purchase.
        db: Database session.

    Returns:
        Dict with order details including razorpay_order_id.
    """
    client = _get_razorpay_client()

    # Create order on Razorpay
    order_data = {
        "amount": amount_paise,
        "currency": currency,
        "notes": {
            "plan_id": plan_id,
            "user_id": user_id,
        },
    }

    razorpay_order = client.order.create(data=order_data)
    logger.info(f"Razorpay order created: {razorpay_order['id']} for user {user_id}, plan {plan_id}")

    # Create subscription record
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        razorpay_order_id=razorpay_order["id"],
        status="created",
        amount=amount_paise,
        currency=currency,
    )
    db.add(subscription)

    # Create payment record
    payment = Payment(
        user_id=user_id,
        subscription_id=subscription.id,
        razorpay_order_id=razorpay_order["id"],
        amount=amount_paise,
        currency=currency,
        status="created",
    )
    db.add(payment)
    db.commit()
    db.refresh(subscription)

    return {
        "order_id": razorpay_order["id"],
        "amount": amount_paise,
        "currency": currency,
        "plan_id": plan_id,
        "subscription_id": subscription.id,
        "key_id": settings.razorpay_key_id,
    }


def verify_payment(order_id: str, payment_id: str, signature: str, db: Session) -> dict:
    """
    Verify Razorpay payment signature using HMAC SHA256.

    Args:
        order_id: Razorpay order ID.
        payment_id: Razorpay payment ID.
        signature: Razorpay signature to verify.
        db: Database session.

    Returns:
        Dict with verification status and subscription details.

    Raises:
        ValueError: If signature verification fails.
    """
    # Verify signature using HMAC SHA256
    message = f"{order_id}|{payment_id}"
    expected_signature = hmac.new(
        key=settings.razorpay_key_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        logger.warning(f"Payment signature verification failed for order {order_id}")
        raise ValueError("Invalid payment signature")

    # Update subscription
    subscription = (
        db.query(Subscription)
        .filter(Subscription.razorpay_order_id == order_id)
        .first()
    )

    if not subscription:
        raise ValueError(f"Subscription not found for order {order_id}")

    subscription.razorpay_payment_id = payment_id
    subscription.status = "active"
    subscription.started_at = datetime.utcnow()
    subscription.expires_at = datetime.utcnow() + timedelta(days=30)

    # Update payment record
    payment = (
        db.query(Payment)
        .filter(Payment.razorpay_order_id == order_id)
        .first()
    )

    if payment:
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = "captured"

    db.commit()
    db.refresh(subscription)

    logger.info(f"Payment verified for order {order_id}, subscription {subscription.id} activated")

    return {
        "subscription_id": subscription.id,
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "started_at": subscription.started_at.isoformat(),
        "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
    }


def get_subscription_status(user_id: str, db: Session) -> dict:
    """
    Get the current subscription status for a user.

    Args:
        user_id: The user ID.
        db: Database session.

    Returns:
        Dict with current plan details and status.
    """
    # Get the most recent active subscription
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if not subscription:
        # Return free plan as default
        free_plan = get_plan_by_id("free")
        return {
            "plan_id": "free",
            "plan_name": free_plan["name"],
            "status": "active",
            "docs_per_month": free_plan["docs_per_month"],
            "features": free_plan["features"],
            "subscription_id": None,
            "started_at": None,
            "expires_at": None,
        }

    # Check if subscription has expired
    if subscription.expires_at and subscription.expires_at < datetime.utcnow():
        subscription.status = "expired"
        db.commit()
        # Return free plan
        free_plan = get_plan_by_id("free")
        return {
            "plan_id": "free",
            "plan_name": free_plan["name"],
            "status": "active",
            "docs_per_month": free_plan["docs_per_month"],
            "features": free_plan["features"],
            "subscription_id": None,
            "started_at": None,
            "expires_at": None,
        }

    plan = get_plan_by_id(subscription.plan_id)
    return {
        "plan_id": subscription.plan_id,
        "plan_name": plan["name"] if plan else subscription.plan_id,
        "status": subscription.status,
        "docs_per_month": plan["docs_per_month"] if plan else 0,
        "features": plan["features"] if plan else [],
        "subscription_id": subscription.id,
        "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
        "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
    }


def handle_webhook_event(event_type: str, payload: dict, db: Session) -> dict:
    """
    Handle Razorpay webhook events.

    Args:
        event_type: The webhook event type (e.g., payment.captured).
        payload: The webhook payload.
        db: Database session.

    Returns:
        Dict with processing status.
    """
    logger.info(f"Processing webhook event: {event_type}")

    if event_type == "payment.captured":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        if order_id:
            subscription = (
                db.query(Subscription)
                .filter(Subscription.razorpay_order_id == order_id)
                .first()
            )
            if subscription and subscription.status != "active":
                subscription.razorpay_payment_id = payment_id
                subscription.status = "active"
                subscription.started_at = datetime.utcnow()
                subscription.expires_at = datetime.utcnow() + timedelta(days=30)

                # Update payment record
                payment = (
                    db.query(Payment)
                    .filter(Payment.razorpay_order_id == order_id)
                    .first()
                )
                if payment:
                    payment.razorpay_payment_id = payment_id
                    payment.status = "captured"

                db.commit()
                logger.info(f"Subscription {subscription.id} activated via webhook")

        return {"status": "processed", "event": event_type}

    elif event_type == "payment.failed":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")

        if order_id:
            payment = (
                db.query(Payment)
                .filter(Payment.razorpay_order_id == order_id)
                .first()
            )
            if payment:
                payment.status = "failed"
                db.commit()
                logger.warning(f"Payment failed for order {order_id}")

        return {"status": "processed", "event": event_type}

    elif event_type == "subscription.activated":
        logger.info("Subscription activated event received")
        return {"status": "processed", "event": event_type}

    elif event_type == "subscription.cancelled":
        logger.info("Subscription cancelled event received")
        return {"status": "processed", "event": event_type}

    else:
        logger.info(f"Unhandled webhook event: {event_type}")
        return {"status": "ignored", "event": event_type}


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify Razorpay webhook signature.

    Args:
        body: Raw request body bytes.
        signature: X-Razorpay-Signature header value.

    Returns:
        True if signature is valid, False otherwise.
    """
    if not settings.razorpay_webhook_secret:
        logger.error("Razorpay webhook secret not configured")
        return False

    expected_signature = hmac.new(
        key=settings.razorpay_webhook_secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
