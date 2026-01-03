from pathlib import Path

TEMPLATE_PATH = Path("app/templates")

def get_available_templates():
    return [f.stem for f in TEMPLATE_PATH.glob("*.tex")]

def load_template(template_name: str):
    file = TEMPLATE_PATH / f"{template_name}.tex"
    if not file.exists():
        raise ValueError("Template not found")
    return file.read_text(encoding="utf-8")
