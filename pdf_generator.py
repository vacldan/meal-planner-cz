"""
PDF generation from meal plan
"""

from jinja2 import Template, Environment, FileSystemLoader
from weasyprint import HTML
import json

def generate_pdf(meal_plan: dict, output_path: str = "meal_plan.pdf"):
    """Generate PDF from meal plan data"""

    # Load template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('meal_plan_template.html')

    # Render HTML
    html_content = template.render(**meal_plan)

    # Generate PDF
    HTML(string=html_content).write_pdf(output_path)
    print(f"✅ PDF vygenerováno: {output_path}")

    return output_path
