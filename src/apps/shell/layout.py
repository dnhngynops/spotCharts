"""
Shell layout — shared Jinja2 Environment for the app.

All app generators import get_env() so that {% include %} directives in
templates resolve correctly against the templates/ directory.
"""
import os
from jinja2 import Environment, FileSystemLoader

# Absolute path to the project-level templates/ directory.
# This file lives at src/apps/shell/layout.py, so we go up 4 levels.
TEMPLATES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates')
)


def get_env() -> Environment:
    """Return a Jinja2 Environment configured for the templates/ directory.

    Using FileSystemLoader enables {% include %} across template files.
    autoescape is disabled because all HTML escaping is done explicitly in
    the Python generators before values are injected.
    """
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
    )
