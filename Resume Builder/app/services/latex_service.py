import subprocess
import os
from pathlib import Path
import uuid
import re
from jinja2 import Environment, FileSystemLoader, BaseLoader
from typing import Dict

# ----------------- CONFIGURATION -----------------
BUILD_DIR = Path("app/build")
TEMPLATE_PATH = Path("app/templates")

BUILD_DIR.mkdir(parents=True, exist_ok=True)

# Global Jinja2 environment (MUST be defined here)
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


# Custom LaTeX escape filter
def latex_escape(value):
    if not value:
        return ""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
    }
    for k, v in replacements.items():
        value = value.replace(k, v)
    return value
# Register the filter
env.filters["latex_escape"] = latex_escape

# ----------------- HELPER FUNCTIONS -----------------
def load_template(template_name: str) -> str:
    file = TEMPLATE_PATH / f"{template_name}.tex"
    if not file.exists():
        raise ValueError(f"Template '{template_name}' not found")
    return file.read_text(encoding="utf-8")

# ----------------- MAIN FUNCTION -----------------
def generate_pdf_from_latex(template_name: str, resume_data: Dict) -> str:
    latex_raw = load_template(template_name)
    
    # Use the GLOBAL env
    template = env.from_string(latex_raw)
    latex_filled = template.render(**resume_data)

    job_id = uuid.uuid4().hex
    tex_path = BUILD_DIR / f"{job_id}.tex"
    pdf_path = BUILD_DIR / f"{job_id}.pdf"

    tex_path.write_text(latex_filled, encoding="utf-8")

    # Compile with configurable tex binary (e.g., xelatex or TinyTeX)
    from app.core.config import settings
    tex_bin = settings.TEX_BIN if getattr(settings, 'TEX_BIN', None) else os.getenv('TEX_BIN', 'xelatex')

    try:
        result = subprocess.run(
            [tex_bin, "-no-shell-escape", "-interaction=nonstopmode", "-output-directory", str(BUILD_DIR), str(tex_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as e:
        # Kill any leftover processes? subprocess handles it, but log for debugging
        raise RuntimeError(f"LaTeX compilation timed out for template '{template_name}'.") from e

    if result.returncode != 0 or not pdf_path.exists():
        debug_out = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        print("---- LaTeX Compilation Output ----")
        print(debug_out)
        raise RuntimeError(f"PDF generation failed for template '{template_name}'. LaTeX error: {result.stderr}")

    return str(pdf_path)