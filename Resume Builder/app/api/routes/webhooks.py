import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import User, PlanEnum, Subscription
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.post("/")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(
        await request.body(),
        sig_header,
        settings.STRIPE_WEBHOOK_SECRET
    )
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(400, "Invalid webhook")

    # -------------------------------
    # PAYMENT SUCCESS
    # -------------------------------
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        if session["mode"] != "subscription":
            return {"status": "ignored"}

        customer_id = session["customer"]
        stripe_subscription_id = session["subscription"]

        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return {"status": "user_not_found"}

        # Fetch subscription to get price_id
        sub = stripe.Subscription.retrieve(stripe_subscription_id)
        price_id = sub["items"]["data"][0]["price"]["id"]

        if price_id == settings.PRO_PRICE_ID:
            plan = PlanEnum.pro
            api_calls = 12
            downloads = 100000
        elif price_id == settings.PRO_PLUS_PRICE_ID:
            plan = PlanEnum.pro_plus
            api_calls = 100000
            downloads = 100000
        else:
            return {"status": "unknown_price"}

        # Prevent duplicate subscriptions
        existing = db.query(Subscription).filter_by(stripe_subscription_id=stripe_subscription_id).first()
        if not existing:
            db.add(Subscription(
                user_id=user.id,
                stripe_subscription_id=stripe_subscription_id,
                plan=plan,
                status="active"
            ))

        # Apply entitlements
        user.plan = plan
        user.api_calls = api_calls
        user.downloads = downloads
        user.stripe_subscription_id = stripe_subscription_id

        db.commit()

    # -------------------------------
    # CANCELLATION / EXPIRE
    # -------------------------------
    if event["type"] in ["customer.subscription.deleted", "customer.subscription.expired"]:
        sub = event["data"]["object"]

        user = db.query(User).filter(User.stripe_subscription_id == sub["id"]).first()
        if user:
            user.plan = PlanEnum.free
            user.api_calls = 2
            user.downloads = 1
            user.stripe_subscription_id = None
            db.commit()

    return {"status": "success"}

