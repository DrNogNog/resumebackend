from fastapi import HTTPException
from app.db.models import User

def require_pro(user: User):
    if user.plan not in ["pro", "pro_plus"]:
        raise HTTPException(status_code=403, detail="Upgrade to Pro to access this feature")
