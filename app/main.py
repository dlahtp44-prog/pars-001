from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.paths import STATIC_DIR
from app.db import init_db

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

# =========================
# SESSION (로그인용)
# =========================
app.add_middleware(
    SessionMiddleware,
    secret_key="pars-wms-secret-key",  # 내부용
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

app.include_router(login_router)      # 로그인 먼저
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

# =========================
# MOBILE
# =========================
from app.pages.mobile_home import router as mobile_home_router
from app.pages.mobile_qr import router as mobile_qr_router
from app.pages.mobile_qr_inventory import router as mobile_qr_inventory_router
from app.pages.mobile_inventory_detail import router as mobile_inventory_detail_router
from app.pages.mobile_move import router as mobile_move_router
from app.pages.mobile_cs import router as mobile_cs_router

app.include_router(mobile_home_router)
app.include_router(mobile_qr_router)
app.include_router(mobile_qr_inventory_router)
app.include_router(mobile_inventory_detail_router)
app.include_router(mobile_move_router)
app.include_router(mobile_cs_router)

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
from app.routers.api_admin import router as api_admin_router  # ✅ 추가

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
app.include_router(api_admin_router)  # ✅ 재고/이력 초기화
