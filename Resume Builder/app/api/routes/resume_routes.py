from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.models import User, HarvardResumeInput, Resume, MITResumeInput, StanfordResumeInput, CosmosResumeInput, CelestialResumeInput, MonochromeResumeInput, NebulaResumeInput, YaleResumeInput
from app.services.latex_service import generate_pdf_from_latex
from app.core.template_registry import get_available_templates
from app.core.database import get_db
import os
from sqlalchemy.future import select
from app.services.auth_service import get_current_user
from typing import List, Optional
from pydantic import BaseModel
router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "resume-builder-api",
        "message": "Service is running normally"
    }

# Pydantic schema for output
class ResumeOut(BaseModel):
    id: int
    name: str
    template: str
    created_at: str

    model_config = {
        "from_attributes": True  # replaces orm_mode in Pydantic v2
    }

@router.get("/{user_id}/resumes")
async def get_user_resumes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Build the query
    result = await db.execute(select(Resume).where(Resume.user_id == user.id))
    
    # Extract all Resume objects
    resumes = result.scalars().all()
    
    return resumes


@router.get("/templates")
def list_templates():
    return {"templates": get_available_templates()}

@router.post("/generate/Harvard")
async def generate_resume(
    data: HarvardResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Harvard', data.dict())

    resume = Resume(
        name=data.name,
        template='Harvard',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/MIT")
async def generate_resume(
    data: MITResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('MIT', data.dict())
    resume = Resume(
        name=data.name,
        template='MIT',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/Stanford")
async def generate_resume(
    data: StanfordResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Stanford', data.dict())

    resume = Resume(
        name=data.name,
        template='Stanford',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/Yale")
async def generate_resume(
    data: YaleResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Yale', data.dict())

    resume = Resume(
        name=data.full_name,
        template='Yale',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/Cosmos")
async def generate_resume(
    data: CosmosResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Cosmos', data.dict())

    resume = Resume(
        name=data.name,
        template='Cosmos',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/Monochrome")
async def generate_resume(
    data: MonochromeResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Monochrome', data.dict())

    resume = Resume(
        name=data.name,
        template='Monochrome',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/Nebula")
async def generate_resume(
    data: NebulaResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Nebula', data.dict())

    resume = Resume(
        name=data.name,
        template='Nebula',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

@router.post("/generate/Celestial")
async def generate_resume(
    data: CelestialResumeInput,
    db: AsyncSession = Depends(get_db)
):
    pdf_path = generate_pdf_from_latex('Celestial', data.dict())

    resume = Resume(
        name=data.name,
        template='Celestial',
        payload=data.dict()
    )

    # db.add(resume)
    # await db.commit()

    return FileResponse(pdf_path, filename="resume.pdf")

class SaveResumeRequest(BaseModel):
    template: str
    name: Optional[str] = None
    payload: dict

@router.post("/save")
async def save_resume_api(
    req: SaveResumeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Generate PDF file from template and payload
    pdf_path = generate_pdf_from_latex(req.template, req.payload)

    # Create Resume record and save path
    resume = Resume(
        user_id=current_user.id,
        name=req.name or req.payload.get("name") or "Untitled",
        template=req.template,
        payload=req.payload,
        file_path=pdf_path
    )

    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return {"id": resume.id, "file_path": resume.file_path}


@router.get("/download/{resume_id}")
async def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Ensure resume exists and belongs to user
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalars().first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Ensure user has downloads remaining
    if current_user.api_downloads <= 0:
        raise HTTPException(status_code=403, detail="No downloads remaining")

    # Decrement download quota
    current_user.api_downloads -= 1
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    filename = os.path.basename(resume.file_path)
    return FileResponse(resume.file_path, filename=filename)


@router.post("/use")
async def use_resume_api(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.api_calls <= 0:
        raise HTTPException(status_code=403, detail="No API calls remaining")

    current_user.api_calls -= 1
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return {"detail": "API call registered"}
