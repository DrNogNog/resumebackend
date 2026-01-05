import subprocess
import os
from pathlib import Path
import uuid
import re
from jinja2 import Environment, FileSystemLoader, BaseLoader
from typing import Dict

# ----------------- CONFIGURATION -----------------
TEMPLATE_PATH = Path("app/templates")

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
import tempfile

def generate_pdf_from_latex(template_name: str, resume_data: Dict) -> bytes:
    """Render LaTeX template, compile it in a temporary directory, and return PDF bytes.

    This avoids writing files to a persistent build folder and is safe for storing
    output directly in a database backend.
    """
    latex_raw = load_template(template_name)

    # Use the GLOBAL env
    template = env.from_string(latex_raw)
    latex_filled = template.render(**resume_data)

    job_id = uuid.uuid4().hex

    # Compile with configurable tex binary (e.g., xelatex or TinyTeX)
    from app.core.config import settings
    tex_bin = settings.TEX_BIN if getattr(settings, 'TEX_BIN', None) else os.getenv('TEX_BIN', 'xelatex')

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tex_path = tmpdir_path / f"{job_id}.tex"
        pdf_path = tmpdir_path / f"{job_id}.pdf"

        tex_path.write_text(latex_filled, encoding="utf-8")

        try:
            result = subprocess.run(
                [tex_bin, "-no-shell-escape", "-interaction=nonstopmode", "-output-directory", str(tmpdir_path), str(tex_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired as e:
            # subprocess will already handle killing the child process; raise a clearer error
            raise RuntimeError(f"LaTeX compilation timed out for template '{template_name}'.") from e

        if result.returncode != 0 or not pdf_path.exists():
            debug_out = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            print("---- LaTeX Compilation Output ----")
            print(debug_out)
            raise RuntimeError(f"PDF generation failed for template '{template_name}'. LaTeX error: {result.stderr}")

        pdf_bytes = pdf_path.read_bytes()

    return pdf_bytes