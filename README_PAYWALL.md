# Stripe + FastAPI paywall

This branch adds an example end-to-end Stripe subscription paywall integrated with FastAPI for the Trade-Scanner-2 project.

Key points
- Uses Stripe Checkout for subscription signups.
- Uses Stripe webhooks to keep a minimal subscription record in a local database.
- Example protected endpoint: GET /premium-data — send X-User-Email header to identify user in this demo.

Environment variables
- STRIPE_SECRET_KEY=sk_test_...
- STRIPE_PUBLISHABLE_KEY=pk_test_...
- STRIPE_WEBHOOK_SECRET=whsec_... (set after running `stripe listen` or from the Stripe dashboard)
- STRIPE_PRICE_ID=price_... (create a recurring price in Stripe and put its ID here)
- DATABASE_URL (defaults to sqlite:///./dev_paywall.db)
- FRONTEND_BASE (defaults to http://localhost:8000)

Running locally
1. Install deps: pip install -r requirements.txt
2. Start app: uvicorn app.main:app --reload
3. Run Stripe CLI to forward webhooks (recommended):
   stripe listen --forward-to localhost:8000/payments/webhook

Creating Stripe product/price
1. In the Stripe Dashboard create a Product (e.g., "TradeScanner Premium").
2. Under that product create a recurring Price (monthly or yearly). Copy the Price ID and set STRIPE_PRICE_ID.

Notes
- This is a minimal reference implementation. Replace the simple X-User-Email header flow with your real auth/user system and integrate stripe_customer_id into your existing User model.
- Do NOT commit real Stripe secret keys. Use repository secrets for production deployments.
