from pathlib import Path

# app/core/paths.py
# 프로젝트 내 경로 표준화 (Railway/로컬 공통)

# .../app/core/paths.py -> parents[1] == app/
BASE_DIR = Path(__file__).resolve().parents[1]

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "wms.db"
