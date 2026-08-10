from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
import os
import json
from payments.stripe_service import create_checkout_session, construct_event, create_billing_portal_session, retrieve_subscription
from models.models import get_db, User, Subscription
from sqlalchemy.orm import Session

router = APIRouter()

FRONTEND_BASE = os.getenv("FRONTEND_BASE", "http://localhost:8000")
DEFAULT_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_monthly_xxx")


@router.post("/create-checkout-session")
async def create_checkout(body: dict, db: Session = Depends(get_db)):
    """Create a Checkout Session. Expects JSON: {"email": "user@example.com", "price_id": "price_..."}
    Returns the Checkout Session URL to redirect the user to.
    """
    email = body.get("email")
    price_id = body.get("price_id", DEFAULT_PRICE_ID)
    if not email:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="email is required")

    success_url = f"{FRONTEND_BASE}/checkout-success"
    cancel_url = f"{FRONTEND_BASE}/checkout-cancel"

    session = create_checkout_session(customer_email=email, success_url=success_url, cancel_url=cancel_url, price_id=price_id, metadata={"email": email})

    # Ensure a user record exists (minimal integration)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, stripe_customer_id=session.get("customer"))
        db.add(user)
        db.commit()

    return {"checkout_url": session.url}


@router.post("/billing-portal")
async def billing_portal(body: dict, db: Session = Depends(get_db)):
    """Create a Billing Portal session. Expects {"email": "..."} and returns url."""
    email = body.get("email")
    if not email:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="email is required")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.stripe_customer_id:
        raise HTTPException(status_code=404, detail="customer not found")
    return {"url": create_billing_portal_session(user.stripe_customer_id, return_url=FRONTEND_BASE + "/") .url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = construct_event(payload, sig_header)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "invalid webhook"})

    # Handle the event types we care about
    type = event.type
    data = event.data.object

    if type == "checkout.session.completed":
        # A Checkout Session has completed. We can link customer -> subscription.
        session = data
        customer_email = session.get("customer_email") or session.get("metadata", {}).get("email")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        if customer_email and subscription_id:
            # Retrieve subscription to get status and period end
            try:
                sub = retrieve_subscription(subscription_id)
            except Exception:
                sub = None
            user = db.query(User).filter(User.email == customer_email).first()
            if user:
                user.stripe_customer_id = customer_id
                # upsert subscription
                existing = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                if not existing:
                    existing = Subscription(user_id=user.id, stripe_subscription_id=subscription_id, status=(sub.status if sub else "active"), current_period_end=getattr(sub, "current_period_end", None))
                    db.add(existing)
                else:
                    existing.stripe_subscription_id = subscription_id
                    existing.status = sub.status if sub else existing.status
                    existing.current_period_end = getattr(sub, "current_period_end", existing.current_period_end)
                db.commit()

    elif type in ("invoice.payment_succeeded", "customer.subscription.updated", "customer.subscription.deleted"):
        # Keep subscription record in sync
        sub = data
        subscription_id = sub.get("id")
        # Find subscription row
        row = db.query(Subscription).filter(Subscription.stripe_subscription_id == subscription_id).first()
        if row:
            row.status = sub.get("status", row.status)
            row.current_period_end = sub.get("current_period_end", row.current_period_end)
            db.commit()

    return {"received": True}


@router.get("/checkout-success")
async def checkout_success():
    return {"status": "success"}


@router.get("/checkout-cancel")
async def checkout_cancel():
    return {"status": "cancelled"}
