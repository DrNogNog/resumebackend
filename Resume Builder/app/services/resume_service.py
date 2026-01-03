from jinja2 import Template
from app.core.template_registry import load_template

def generate_resume_html(template_name: str, resume_data: dict):
    raw_html = load_template(template_name)
    template = Template(raw_html)
    return template.render(**resume_data)
