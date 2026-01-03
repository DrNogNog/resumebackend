from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.db.models import Resume

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "resume-builder-api",
        "message": "Service is running normally"
    }

@router.get("/")
def read_users():
    return {"message": "Users route working"}


