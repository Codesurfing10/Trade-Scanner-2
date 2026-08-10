import os
import json
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


def create_checkout_session(customer_email: str, success_url: str, cancel_url: str, price_id: str, metadata: dict = None):
    """Create a Stripe Checkout session for a subscription."""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=customer_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata or {},
    )
    return session


def create_billing_portal_session(customer_id: str, return_url: str):
    """Create a Stripe Billing Portal session for a customer."""
    session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
    return session


def construct_event(payload: bytes, sig_header: str):
    """Verify and construct a Stripe event using the webhook signing secret.
    If STRIPE_WEBHOOK_SECRET is not set (local quickstart), this will fall back to parsing the payload.
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return event
        except Exception as e:
            raise
    # Fallback (unsigned) - only for local testing with the CLI when you don't want to use signatures
    try:
        data = json.loads(payload.decode("utf-8"))
        return stripe.Event.construct_from(data, stripe.api_key)
    except Exception:
        raise


def retrieve_subscription(subscription_id: str):
    return stripe.Subscription.retrieve(subscription_id)
