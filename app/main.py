from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from payments.routes import router as payments_router
from models.models import Base, engine, get_db, User, Subscription
from sqlalchemy.orm import Session
import os

app = FastAPI(title="Trade Scanner - Paywall Example")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount payments router
app.include_router(payments_router, prefix="/payments")


# Create tables on startup (simple convenience)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# Simple protected endpoint that requires an active subscription
@app.get("/premium-data")
def premium_data(x_user_email: str = Header(None), db: Session = Depends(get_db)):
    if not x_user_email:
        raise HTTPException(status_code=401, detail="X-User-Email header required for demo")
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user:
        raise HTTPException(status_code=403, detail="user not found")
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).order_by(Subscription.id.desc()).first()
    if not sub or sub.status not in ("active", "trialing"):
        raise HTTPException(status_code=402, detail="subscription required")
    return {"message": "here is your premium data", "sample": [1, 2, 3]}


# A minimal health endpoint
@app.get("/")
def health():
    return {"ok": True}
