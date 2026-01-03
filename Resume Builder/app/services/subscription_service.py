import stripe
from sqlalchemy.orm import Session
from app.db.models import User, Subscription, PlanEnum
from app.core.config import settings
import anyio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

stripe.api_key = settings.STRIPE_API_KEY

# Map paid plans to Stripe Price IDs
PRICE_MAP = {
    PlanEnum.pro.value: settings.PRO_PRICE_ID,
    PlanEnum.pro_plus.value: settings.PRO_PLUS_PRICE_ID
}

async def get_active_plan(db: AsyncSession, user_id: int) -> PlanEnum:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
    )
    active_sub = result.scalar_one_or_none()
    return active_sub.plan if active_sub else PlanEnum.free

def ensure_stripe_customer(user: User) -> str:
    """
    Create a Stripe customer if the user doesn't have one yet.
    Returns the Stripe customer ID.
    """
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.name)
        user.stripe_customer_id = customer.id
    return user.stripe_customer_id

async def start_subscription(user: User, plan: str, db: Session):
    """
    Creates a subscription for a user.
    - If plan is 'free', just create a DB subscription without Stripe.
    - For paid plans, create a Stripe subscription and return client_secret.
    """
    # Handle free plan
    if plan == PlanEnum.free.value:
        # Check if user already has a free subscription
        existing = db.query(Subscription).filter_by(user_id=user.id, plan=plan).first()
        if existing:
            return {"subscription": existing, "client_secret": None}

        db_subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=None,
            plan=plan,
            status="active"
        )
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        return {"subscription": db_subscription, "client_secret": None}

    # Paid plan: make sure Stripe customer exists
    customer_id = ensure_stripe_customer(user)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Get Stripe Price ID
    if plan not in PRICE_MAP:
        raise ValueError(f"Unknown plan: {plan}")
    price_id = PRICE_MAP[plan]

    # Create Stripe subscription in a separate thread
    sub = await anyio.to_thread.run_sync(
        lambda: stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
    )

    # Extract client secret for frontend payment confirmation
    client_secret = None
    if getattr(sub.latest_invoice, "payment_intent", None):
        client_secret = sub.latest_invoice.payment_intent.client_secret

    # Save subscription in DB
    db_subscription = Subscription(
        user_id=user.id,
        stripe_subscription_id=sub.id,
        plan=plan,
        status=sub.status
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)

    return {"subscription": db_subscription, "client_secret": client_secret}
