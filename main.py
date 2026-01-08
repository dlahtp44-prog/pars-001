from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

# =====================================================
# FastAPI APP
# =====================================================

app = FastAPI(
    title="PARS WMS",
    version="1.6.6-qr"
)


@app.on_event("startup")
def on_startup():
    """
    서비스 기동 시 1회 실행
    - DB 초기화 / 마이그레이션
    """
    init_db()


# =====================================================
# STATIC FILES
# =====================================================

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


# =====================================================
# PC PAGE ROUTERS
# =====================================================

from app.pages.index_page import router as index_router
from app.pages.inbound_page import router as inbound_page_router
from app.pages.outbound_page import router as outbound_page_router
from app.pages.move_page import router as move_page_router
from app.pages.inventory_page import router as inventory_page_router
from app.pages.history_page import router as history_page_router
from app.pages.location_page import router as location_page_router
from app.pages.opening_page import router as opening_page_router
from app.pages.admin_page import router as admin_page_router
from app.pages.qr_page import router as qr_page_router
from app.pages.test_page import router as test_page_router

app.include_router(index_router)
app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(location_page_router)
app.include_router(opening_page_router)
app.include_router(admin_page_router)
app.include_router(qr_page_router)
app.include_router(test_page_router)


# =====================================================
# MOBILE PAGE ROUTERS
# =====================================================

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


# =====================================================
# API ROUTERS
# =====================================================

from app.routers.api_inbound import router as api_inbound_router
from app.routers.api_outbound import router as api_outbound_router
from app.routers.api_move import router as api_move_router
from app.routers.api_inventory import router as api_inventory_router
from app.routers.api_history import router as api_history_router
from app.routers.api_damage import router as api_damage_router
from app.routers.api_damage_codes import router as api_damage_codes_router
from app.routers.excel_inbound import router as api_excel_inbound_router
from app.routers.excel_outbound import router as api_excel_outbound_router

app.include_router(api_inbound_router)
app.include_router(api_outbound_router)
app.include_router(api_move_router)
app.include_router(api_inventory_router)
app.include_router(api_history_router)
app.include_router(api_damage_router)
app.include_router(api_damage_codes_router)
app.include_router(api_excel_inbound_router)
app.include_router(api_excel_outbound_router)
