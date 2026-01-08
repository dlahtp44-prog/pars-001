from pathlib import Path

# app/core/paths.py
BASE_DIR = Path(__file__).resolve().parent.parent

APP_DIR = BASE_DIR
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
DATA_DIR = APP_DIR / "data"
