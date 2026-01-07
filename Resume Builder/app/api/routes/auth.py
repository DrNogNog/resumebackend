# FastAPI & Pydantic
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel, EmailStr
import os
from fastapi.responses import RedirectResponse
# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
# App services
from app.services.auth_service import (
    authenticate_user,
    signup_user,
    create_access_token,
    verify_user,
    create_password_reset_token,
    reset_password,
    create_refresh_token,
    verify_refresh_token,
    rotate_refresh_token,
    send_verification_email_async,
    get_current_user,
    get_current_user_optional
)

# Database
from app.core.database import get_db
from app.core.sync_database import get_db_sync
from app.db.models import User, Subscription, PlanEnum  # Ensure your User model is imported
from sqlalchemy.future import select
# Python standard library
import asyncio

router = APIRouter()

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

@router.post("/signup")
async def signup(
    payload: SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Create user in DB (no 'plan' argument)
        user = await signup_user(
            db,
            name=payload.name,
            email=payload.email,
            password=payload.password
        )

        # 2️⃣ Schedule async email sending
        background_tasks.add_task(
            send_verification_email_async,
            user.email,
            user.verification_token
        )
        

        verification_url = f"https://api.resumesub.xyz/verify-email?token={user.verification_token}"

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "User created, please verify your email",
        "verification_token": user.verification_token,
        "verification_url": verification_url
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db_sync),
):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token(db, user)

    # ----- Ensure subscription -----
    subscription = next((s for s in user.subscriptions if s.status == "active"), None)
    if not subscription:
        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id="free_plan",
            plan=PlanEnum.free,
            status="active",
        )
        db.add(subscription)
        db.commit()
        db.refresh(user)

    # 🔥 WRITE COOKIE HERE
    # Use secure cookies only in production
    secure_cookie = os.getenv("ENV", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )

    return {
        "message": "Login successful",
        "user_id": user.id,
        "plan": subscription.plan.value,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

FRONTEND_URL = "https://www.resumesub.xyz"  # your frontend domain

@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verifies a user's email using the token provided in the request body.
    Returns JSON so the frontend can display status messages.
    """
    # 1️⃣ Find user by verification token
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalars().first()

    if not user:
        # Token invalid or already used
        return {"status": "error", "message": "Invalid or expired token"}

    if user.is_verified:
        # User already verified
        return {"status": "already_verified", "message": "Email already verified"}

    # 2️⃣ Mark user as verified
    user.is_verified = True
    user.verification_token = None  # remove token after use
    await db.commit()

    # 3️⃣ Return success JSON
    return {"status": "success", "message": "Email verified successfully!"}


@router.post("/request-password-reset")
def request_password_reset(email: str, db: Session = Depends(get_db_sync)):
    token = create_password_reset_token(db, email)
    if not token:
        raise HTTPException(status_code=404, detail="Email not found")
    # TODO: Send token via email
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
def reset_user_password(token: str, new_password: str, db: Session = Depends(get_db_sync)):
    success = reset_password(db, token, new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Password reset successfully"}


@router.post("/refresh-token")
def refresh_user_token(user_id: int, refresh_token: str, db: Session = Depends(get_db_sync)):
    if not verify_refresh_token(db, user_id, refresh_token):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token({"sub": user.email})
    new_refresh_token = rotate_refresh_token(db, user)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": user.id
    }

@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db_sync), current_user = Depends(get_current_user_optional)):
    """
    Clears the refresh token in DB and deletes cookie.
    current_user is optional, so logout always works.
    """
    if current_user:
        current_user.refresh_token_hash = None
        current_user.refresh_token_expires = None
        db.commit()
    # delete refresh token cookie if using cookies
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}