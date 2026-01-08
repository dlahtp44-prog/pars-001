from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

app = FastAPI(title="PARS WMS", version="1.6.6-qr")

@app.on_event("startup")
def on_startup():
    init_db()

# Static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# =========================
# Page routers (PC)
# =========================
from app.pages.index_page import router as index_page_router
from app.pages.inbound_page import router as inbound_page_router
from app.pages.outbound_page import router as outbound_page_router
from app.pages.move_page import router as move_page_router
from app.pages.inventory_page import router as inventory_page_router
from app.pages.history_page import router as history_page_router
from app.pages.location_page import router as location_page_router
from app.pages.qr_page import router as qr_page_router
from app.pages.opening_page import router as opening_page_router
from app.pages.admin_page import router as admin_page_router
from app.pages.test_page import router as test_page_router

app.include_router(index_page_router)
app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(location_page_router)
app.include_router(qr_page_router)
app.include_router(opening_page_router)
app.include_router(admin_page_router)
app.include_router(test_page_router)

# =========================
# API routers
# =========================
from app.routers.inbound import router as api_inbound_router
from app.routers.outbound import router as api_outbound_router
from app.routers.move import router as api_move_router
from app.routers.inventory import router as api_inventory_router
from app.routers.history import router as api_history_router
from app.routers.items import router as api_items_router
from app.routers.location import router as api_location_router
from app.routers.qr_api import router as api_qr_router

app.include_router(api_inbound_router)
app.include_router(api_outbound_router)
app.include_router(api_move_router)
app.include_router(api_inventory_router)
app.include_router(api_history_router)
app.include_router(api_items_router)
app.include_router(api_location_router)
app.include_router(api_qr_router)
