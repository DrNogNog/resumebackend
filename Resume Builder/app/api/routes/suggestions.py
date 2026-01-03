# routes/suggestions.py
from fastapi import APIRouter, UploadFile, Form, File, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import Suggestion
import shutil, time, os

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/suggestions")
async def create_suggestion(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    filename = None

    if file:
        filename = f"{int(time.time())}-{file.filename}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    suggestion = Suggestion(
        title=title,
        description=description,
        file=filename
    )

    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return {"success": True, "id": suggestion.id}
