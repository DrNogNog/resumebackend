from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.services.ollama_service import call_ollama, generate_match_prompt, generate_resume_prompt, generate_sw_prompt
from app.db.models import GenerateRequest, User
from app.services.usage_service import check_llm_usage
from app.services.extraction_service import extract_resume_text
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import get_current_user
import httpx

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "resume-builder-api",
        "message": "Service is running normally"
    }


@router.get("/health/tex", tags=["Health"])
async def health_tex():
    """Run the configured TeX binary (e.g., xelatex) with --version and return its output.
    Returns 200 when available, 503 when missing or failing.
    """
    from app.core.config import settings
    import subprocess

    tex_bin = getattr(settings, "TEX_BIN", None) or "xelatex"

    try:
        proc = subprocess.run([tex_bin, "--version"], capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        # binary not found on PATH
        raise HTTPException(status_code=503, detail=f"TeX binary '{tex_bin}' not found on PATH")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=503, detail=f"TeX binary '{tex_bin}' timed out")

    if proc.returncode != 0:
        raise HTTPException(status_code=503, detail=(proc.stderr or proc.stdout).strip()[:400])

    # return first line of version info
    first_line = (proc.stdout or proc.stderr).splitlines()[0]
    return {"tex": tex_bin, "version": first_line}


@router.post("/")
async def generate(
    resume_text: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    job_description: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # <-- requires login
):
    # ---------- Check API usage ----------
    if not check_llm_usage(db, current_user):
        raise HTTPException(
            status_code=403,
            detail="API call limit reached. Upgrade your plan."
        )

    if resume_file:
        resume_text = await extract_resume_text(resume_file)
    elif not resume_text:
        raise HTTPException(status_code=400, detail="Please provide either resume text or a file.")

    # ---------- Call Ollama ----------
    try:
        prompt_one = await generate_resume_prompt(resume_text, job_description)
        prompt_two = await generate_sw_prompt(resume_text, job_description)
        prompt_three = await generate_match_prompt(resume_text, job_description)

        one = await call_ollama(prompt_one)
        two = await call_ollama(prompt_two)
        three = await call_ollama(prompt_three)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="LLM service is currently unavailable. Please try again later."
        )

    return {
        "match_summary": one,
        "strengths_weaknesses": two,
        "improvement_tips": three
    }