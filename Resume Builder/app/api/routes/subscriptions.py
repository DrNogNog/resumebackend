import stripe
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.models import User, PlanEnum
from app.core.config import settings
from app.core.database import get_db
from sqlalchemy import select

router = APIRouter()
stripe.api_key = settings.STRIPE_API_KEY

PRICE_MAP = {
    "pro": settings.PRO_PRICE_ID,
    "pro_plus": settings.PRO_PLUS_PRICE_ID
}

def get_or_create_stripe_customer(user: User):
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.name)
        user.stripe_customer_id = customer.id
    return user.stripe_customer_id

@router.post("/subscribe/{user_id}/{plan_key}")
async def subscribe(user_id: int, plan_key: str, db: Session = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # Free plan is handled automatically
    if plan_key == "free":
        user.plan = PlanEnum.free
        db.commit()
        return {"message": "Free plan assigned"}

    # Check valid paid plan
    price_id = PRICE_MAP.get(plan_key)
    if not price_id:
        raise HTTPException(400, "Unknown plan")

    # Create Stripe customer if needed
    customer_id = get_or_create_stripe_customer(user)

    # Create Stripe Checkout session
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer=user.stripe_customer_id,
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        success_url=f"{settings.FRONTEND_URL}/account?success=true",
        cancel_url=f"{settings.FRONTEND_URL}/account?canceled=true",
    )

    return {"checkout_url": session.url}
