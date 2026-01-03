import secrets
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
import asyncio
from app.db.models import User, PlanEnum,Subscription
from app.core.database import get_db
import smtplib
from email.mime.text import MIMEText
import logging
from email.mime.multipart import MIMEMultipart
import ssl

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from concurrent.futures import ThreadPoolExecutor
import aiosmtplib
from app.core.sync_database import get_db_sync

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FRONTEND_URL = os.getenv("FRONTEND_URL")
executor = ThreadPoolExecutor(max_workers=2)
logger = logging.getLogger(__name__)

async def send_verification_email_async(user_email: str, token: str):
    verification_url = f"{FRONTEND_URL}/verify-email?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your Resume account"
    msg["From"] = f"Resume <{SMTP_USER}>"
    msg["To"] = user_email

    text_body = f"""
Welcome to Resume!

Verify your email by clicking the link below:

{verification_url}

If you didn't create this account, you can safely ignore this email.
"""

    html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height:1.6;">
    <h2>Welcome to Resume 👋</h2>
    <p>Please verify your email by clicking the button below:</p>
    <p>
      <a href="{verification_url}"
         style="background:#4f46e5;color:#fff;padding:12px 18px;
                text-decoration:none;border-radius:6px;display:inline-block;">
        Verify Email
      </a>
    </p>
    <p>If you didn’t request this, you can ignore this email.</p>
  </body>
</html>
"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()

    try:
        # Explicitly pass hostname and port
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,  # MUST provide this
            port=SMTP_PORT,      # MUST provide this
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS,
            timeout=15
        )
        logger.info(f"✅ Verification email sent to {user_email}")
    except aiosmtplib.SMTPException as e:
        logger.error(f"❌ SMTP error for {user_email}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error for {user_email}: {e}")

# =====================
# Load environment variables
# =====================

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # Route used for login

# =====================
# Password utilities
# =====================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# =====================
# JWT utilities
# =====================
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# =====================
# Refresh token utils
# =====================
def create_refresh_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    user.refresh_token_hash = hash_password(token)
    user.refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()
    db.refresh(user)
    return token
import uuid
def verify_refresh_token(db: Session, user_id: int, token: str) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.refresh_token_hash:
        return False
    if user.refresh_token_expires < datetime.utcnow():
        return False
    return pwd_context.verify(token, user.refresh_token_hash)

def rotate_refresh_token(db: Session, user: User) -> str:
    return create_refresh_token(db, user)

# =====================
# User Management
# =====================
async def signup_user(db: AsyncSession, name: str, email: str, password: str) -> User:
    # 1️⃣ Check if user already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ValueError("Email already registered")

    # 2️⃣ Create verification token
    verification_token = str(uuid.uuid4())

    # 3️⃣ Hash password
    hashed_password = hash_password(password)

    # 4️⃣ Create user instance with default free plan
    user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        verification_token=verification_token,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)

    free_subscription = Subscription(
        user_id=user.id,
        stripe_subscription_id=str(uuid.uuid4()),  # placeholder
        plan=PlanEnum.free,
        status="active"
    )
    db.add(free_subscription)
    await db.commit()
    await db.refresh(free_subscription)
    
    return user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def verify_user(db: Session, token: str) -> Optional[User]:
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        return None
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return user

# =====================
# Password Reset
# =====================
def create_password_reset_token(db: Session, email: str) -> Optional[str]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    token = secrets.token_urlsafe(32)
    user.reset_password_token = token
    user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    return token

def reset_password(db: Session, token: str, new_password: str) -> bool:
    user = db.query(User).filter(User.reset_password_token == token).first()
    if not user:
        return False
    if datetime.utcnow() > user.reset_password_expires:
        return False
    user.hashed_password = hash_password(new_password)
    user.reset_password_token = None
    user.reset_password_expires = None
    db.commit()
    return True

# =====================
# Current user dependency
# =====================

async def get_token_from_request(request: Request, access_token: Optional[str] = Cookie(None)) -> str:
    """Attempt to extract a token from the access_token cookie first, then the Authorization header."""
    # Prefer cookie token
    if access_token:
        return access_token

    # Fallback to Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]

    raise HTTPException(status_code=401, detail="Not authenticated")

async def get_current_user(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    # Use async SQLAlchemy query
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise credentials_exception

    return user


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db_sync)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        return None