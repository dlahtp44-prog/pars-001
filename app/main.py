from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="PARS WMS",
    version="1.6.6-stable"
)

@app.on_event("startup")
def startup():
    init_db()

# =====================================================
# STATIC
# =====================================================

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# =====================================================
# PC PAGES
# =====================================================

from app.pages.index_page import router as index_router
from app.pages.inbound_page import router as inbound_page_router
from app.pages.outbound_page import router as outbound_page_router
from app.pages.move_page import router as move_page_router
from app.pages.inventory_page import router as inventory_page_router
from app.pages.history_page import router as history_page_router
from app.pages.excel_center_page import router as excel_center_page_router
from app.pages.excel_inbound_page import router as excel_inbound_page_router
from app.pages.excel_outbound_page import router as excel_outbound_page_router
from app.pages.damage_page import router as damage_page_router
from app.pages.damage_history_page import router as damage_history_page_router
from app.pages.label_page import router as label_page_router

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
app.include_router(label_page_router)

# =====================================================
# MOBILE PAGES
# =====================================================

from app.pages.mobile.mobile_home_page import router as mobile_home_router
from app.pages.mobile.mobile_qr_page import router as mobile_qr_router
from app.pages.mobile.mobile_inventory_detail_page import router as mobile_inventory_router
from app.pages.mobile.mobile_move_page import router as mobile_move_router
from app.pages.mobile.mobile_cs_page import router as mobile_cs_router

app.include_router(mobile_home_router)
app.include_router(mobile_qr_router)
app.include_router(mobile_inventory_router)
app.include_router(mobile_move_router)
app.include_router(mobile_cs_router)

# =====================================================
# API
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
