from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import User
from app.services.auth_service import get_current_user  # Your auth dependency
from app.services.usage_service import check_api_usage, check_download_usage, check_llm_usage
router = APIRouter()

@router.get("/some-protected-api")
def protected_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_api_usage(db, current_user):
        raise HTTPException(status_code=403, detail="API call limit reached. Upgrade your plan.")

    # Your API logic here
    return {
        "message": "Here’s your data!",
        "user_plan": current_user.plan.name,  # <-- this returns free/pro/plus
        "api_calls_used": current_user.api_calls
    }

@router.get("/some-protected-api-two")
def protected_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_download_usage(db, current_user):
        raise HTTPException(status_code=403, detail="API call limit reached. Upgrade your plan.")

    # Your API logic here
    return {
        "message": "Here’s your data!",
        "user_plan": current_user.plan.name,  # <-- this returns free/pro/plus
        "api_calls_used": current_user.api_downloads
    }

@router.get("/some-protected-api-three")
def protected_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_llm_usage(db, current_user):
        raise HTTPException(status_code=403, detail="API call limit reached. Upgrade your plan.")

    # Your API logic here
    return {
        "message": "Here’s your data!",
        "user_plan": current_user.plan.name,  # <-- this returns free/pro/plus
        "api_calls_used": current_user.api_downloads
    }
