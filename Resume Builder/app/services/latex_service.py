import subprocess
import os
from pathlib import Path
import uuid
import tempfile
from jinja2 import Environment, FileSystemLoader
from typing import Dict

# ----------------- CONFIGURATION -----------------
TEMPLATE_PATH = Path("app/templates")

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_PATH)),
    autoescape=False
)

# ----------------- JINJA2 FILTER -----------------
def latex_escape(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
        .replace("\\", r"\textbackslash{}")
    )

env.filters['latex_escape'] = latex_escape

# ----------------- HELPERS -----------------
def sanitize_payload(obj):
    """Recursively sanitize all strings in user data"""
    if isinstance(obj, dict):
        return {k: sanitize_payload(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_payload(v) for v in obj]
    if isinstance(obj, str):
        return latex_escape(obj)
    return obj

def generate_pdf_from_latex(template_name: str, resume_data: Dict) -> bytes:
    template = env.get_template(f"{template_name}.tex")
    safe_data = sanitize_payload(resume_data)
    latex_filled = template.render(**safe_data)

    job_id = uuid.uuid4().hex
    tex_bin = os.getenv("TEX_BIN", "xelatex")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tex_path = tmpdir_path / f"{job_id}.tex"
        pdf_path = tmpdir_path / f"{job_id}.pdf"

        tex_path.write_text(latex_filled, encoding="utf-8")

        result = subprocess.run(
            [tex_bin, "-no-shell-escape", "-interaction=nonstopmode",
             "-output-directory", str(tmpdir_path), str(tex_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0 or not pdf_path.exists():
            print("----- LaTeX STDOUT -----")
            print(result.stdout)
            print("----- LaTeX STDERR -----")
            print(result.stderr)
            raise RuntimeError(f"PDF generation failed for template '{template_name}'.")

        return pdf_path.read_bytes()
