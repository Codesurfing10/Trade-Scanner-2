### Add Stripe subscription paywall (FastAPI)

This PR adds an example end-to-end Stripe subscription paywall integrated with FastAPI.

What I changed:
- Added payments/stripe_service.py — Stripe helper functions
- Added payments/routes.py — FastAPI endpoints for checkout, billing portal, and webhook
- Added models/models.py — SQLAlchemy User and Subscription models and DB dependency
- Added app/main.py — FastAPI app mounting payment routes and demo protected endpoint
- Added requirements.txt, README_PAYWALL.md, and tests/test_payments.py

Notes and setup instructions are included in README_PAYWALL.md. Do not commit real Stripe keys; use repository secrets for production.
