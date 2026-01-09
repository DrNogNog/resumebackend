import subprocess
import os
from pathlib import Path
import uuid
import tempfile
from jinja2 import Environment, BaseLoader
from typing import Dict

# ----------------- CONFIGURATION -----------------
TEMPLATE_PATH = Path("app/templates")

env = Environment(
    loader=BaseLoader(),
    autoescape=False,
    block_start_string='((*',
    block_end_string='*))',
    variable_start_string='(((',
    variable_end_string=')))',
    comment_start_string='((#',
    comment_end_string='#))',
)

# ----------------- JINJA2 FILTER -----------------

def latex_escape(text: str) -> str:
    """
    Escapes only user-provided text for LaTeX.
    Template LaTeX commands are left intact.
    """
    if not text:
        return ""
    return (
        text.replace("&", r"\&")
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

# Register filter in Jinja2
env.filters['latex_escape'] = latex_escape

# ----------------- HELPERS -----------------

def load_template(template_name: str) -> str:
    file = TEMPLATE_PATH / f"{template_name}.tex"
    if not file.exists():
        raise ValueError(f"Template '{template_name}' not found")
    return file.read_text(encoding="utf-8")

def sanitize_payload(obj):
    """
    Recursively sanitize user payload, keeping template commands intact.
    """
    if isinstance(obj, dict):
        return {k: sanitize_payload(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_payload(v) for v in obj]
    if isinstance(obj, str):
        return latex_escape(obj)
    return obj

# ----------------- MAIN FUNCTION -----------------

def generate_pdf_from_latex(template_name: str, resume_data: Dict) -> bytes:
    latex_raw = load_template(template_name)
    safe_data = sanitize_payload(resume_data)
    template = env.from_string(latex_raw)
    latex_filled = template.render(**safe_data)

    job_id = uuid.uuid4().hex

    from app.core.config import settings
    tex_bin = getattr(settings, "TEX_BIN", os.getenv("TEX_BIN", "xelatex"))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tex_path = tmpdir_path / f"{job_id}.tex"
        pdf_path = tmpdir_path / f"{job_id}.pdf"

        tex_path.write_text(latex_filled, encoding="utf-8")

        try:
            result = subprocess.run(
                [tex_bin, "-no-shell-escape", "-interaction=nonstopmode",
                 "-output-directory", str(tmpdir_path), str(tex_path)],
                capture_output=True,
                text=True,
                timeout=60,  # increase timeout
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"LaTeX compilation timed out for template '{template_name}'.") from e

        # LOG EVERYTHING if failed
        if result.returncode != 0 or not pdf_path.exists():
            print("----- LaTeX STDOUT -----")
            print(result.stdout)
            print("----- LaTeX STDERR -----")
            print(result.stderr)
            raise RuntimeError(f"PDF generation failed for template '{template_name}'.")

        return pdf_path.read_bytes()

