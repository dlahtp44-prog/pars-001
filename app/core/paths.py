from pathlib import Path

# 현재 파일: app/core/paths.py
# 기준 디렉토리를 "프로젝트 루트/app" 로 고정

BASE_DIR = Path(__file__).resolve().parents[2] / "app"

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

# 안전장치
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "wms.db"
