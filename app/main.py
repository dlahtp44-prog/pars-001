from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from app.core.paths import STATIC_DIR
from app.db import init_db, reset_inventory_and_history

app = FastAPI(
    title="PARS WMS",
    version="1.6.6-qr"
)

# =========================
# STARTUP
# =========================
@app.on_event("startup")
def on_startup():
    init_db()

    raw_flag = os.getenv("RESET_DB", "1").strip().lower()
    reset_flag = raw_flag in {"1", "true", "yes", "y", "on"}

    if reset_flag:
        print(f"⚠ RESET_DB={raw_flag} → inventory/history 초기화 실행")
        reset_inventory_and_history()
    else:
        print(f"ℹ RESET_DB={raw_flag} → 데이터 유지")

# =========================
# SESSION
# =========================
app.add_middleware(
    SessionMiddleware,
    secret_key="pars-wms-secret-key",
)

# =========================
# STATIC
# =========================
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# =========================
# PC PAGES
# =========================
from app.pages.index import router as index_router
from app.pages.login import router as login_router
from app.pages.inbound import router as inbound_page_router
from app.pages.outbound import router as outbound_page_router
from app.pages.move import router as move_page_router
from app.pages.inventory import router as inventory_page_router
from app.pages.history import router as history_page_router
from app.pages.excel_center import router as excel_center_page_router
from app.pages.excel_inbound import router as excel_inbound_page_router
from app.pages.excel_outbound import router as excel_outbound_page_router
from app.pages.damage import router as damage_page_router
from app.pages.damage_history import router as damage_history_page_router
from app.pages.labels import router as labels_page_router
from app.pages.erp_verify import router as erp_verify_page_router
from app.pages.calendar import router as calendar_page_router
from app.pages import init_inventory
from app.pages import admin_reset
from app.pages.outbound_summary import router as outbound_summary_router

# ✅ 이력 엑셀 (pandas 없는 버전)
from app.routers.excel_history import router as excel_history_router
from app.routers.api_rollback_batch import router as api_rollback_batch_router
from app.routers import api_admin_reset
from app.routers import api_init_inventory
from app.routers import api_excel_history

app.include_router(login_router)
app.include_router(index_router)
app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(excel_center_page_router)
app.include_router(excel_inbound_page_router)
app.include_router(excel_outbound_page_router)
app.include_router(damage_page_router)
app.include_router(damage_history_page_router)
app.include_router(labels_page_router)
app.include_router(erp_verify_page_router)
app.include_router(calendar_page_router)
app.include_router(api_rollback_batch_router)
app.include_router(api_admin_reset.router)
app.include_router(api_init_inventory.router)
app.include_router(init_inventory.router)
app.include_router(admin_reset.router)
app.include_router(api_excel_history.router)
app.include_router(outbound_summary_router)

# 🔥 이력 엑셀 다운로드
app.include_router(excel_history_router)

# =========================
# MOBILE
# =========================
from app.pages.mobile_home import router as mobile_home_router
from app.pages.mobile_qr import router as mobile_qr_router
from app.pages.mobile_qr_inventory import router as mobile_qr_inventory_router
from app.pages.mobile_inventory_detail import router as mobile_inventory_detail_router
from app.pages.mobile_move import router as mobile_move_router
from app.pages.mobile_cs import router as mobile_cs_router
from app.pages.mobile_calendar import router as mobile_calendar_router

app.include_router(mobile_home_router)
app.include_router(mobile_qr_router)
app.include_router(mobile_qr_inventory_router)
app.include_router(mobile_inventory_detail_router)
app.include_router(mobile_move_router)
app.include_router(mobile_cs_router)
app.include_router(mobile_calendar_router)

# =========================
# API
# =========================
from app.routers.api_inbound import router as api_inbound_router
from app.routers.api_outbound import router as api_outbound_router
from app.routers.api_move import router as api_move_router
from app.routers.api_inventory import router as api_inventory_router
from app.routers.api_history import router as api_history_router
from app.routers.api_damage import router as api_damage_router
from app.routers.api_damage_codes import router as api_damage_codes_router
from app.routers.excel_inbound import router as api_excel_inbound_router
from app.routers.excel_outbound import router as api_excel_outbound_router
from app.routers.api_labels import router as api_labels_router
from app.routers.api_admin import router as api_admin_router
from app.routers.api_rollback import router as api_rollback_router
from app.routers.api_erp_verify import router as api_erp_verify_router
from app.routers.api_excel_outbound_summary import router as api_excel_outbound_summary_router

app.include_router(api_inbound_router)
app.include_router(api_outbound_router)
app.include_router(api_move_router)
app.include_router(api_inventory_router)
app.include_router(api_history_router)
app.include_router(api_damage_router)
app.include_router(api_damage_codes_router)
app.include_router(api_excel_inbound_router)
app.include_router(api_excel_outbound_router)
app.include_router(api_labels_router)
app.include_router(api_admin_router)
app.include_router(api_rollback_router)
app.include_router(api_erp_verify_router)
app.include_router(api_excel_outbound_summary_router)
