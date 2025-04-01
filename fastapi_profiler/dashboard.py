import os
import pathlib

# Get the directory where the static files are located
STATIC_DIR = pathlib.Path(__file__).parent / "static"


def get_template_content(template_path: str) -> str:
    """Read a template file and return its contents."""
    with open(os.path.join(STATIC_DIR, template_path), "r") as f:
        return f.read()


def generate_dashboard_html(dashboard_path: str = "/profiler") -> str:
    """Generate the HTML for the profiler dashboard.

    Args:
        dashboard_path: The base URL path where the dashboard is mounted

    Returns:
        str: The complete HTML for the dashboard
    """
    css_path = f"{dashboard_path}/static/css/styles.css"
    js_path = f"{dashboard_path}/static/js/dashboard.js"

    template = get_template_content("templates/dashboard.html")

    template = template.replace("{{css_path}}", css_path)
    template = template.replace("{{js_path}}", js_path)
    template = template.replace("{{dashboard_path}}", dashboard_path)

    return template
