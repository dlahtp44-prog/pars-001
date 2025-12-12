

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.pages import index_page
from app.routers import (
    items, inbound, outbound, move, location,
    inventory, history, qr_api
)
import os

app = FastAPI(title="PARS WMS - Responsive + QR + Label 70x40")


# ------------------------------------------------------------
# STATIC PATH
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))           # /pars-wms-api
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")            # /pars-wms-api/app/static
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")       # /pars-wms-api/app/templates

# static 폴더 mount
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# templates 객체 선언 (pages에서 사용됨)
templates = Jinja2Templates(directory=TEMPLATE_DIR)


# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# ROUTERS
# ------------------------------------------------------------
app.include_router(index_page.router)
app.include_router(items.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(location.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(qr_api.router)


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------
@app.get("/ping")
def ping():
    return {"status": "OK", "msg": "PARS WMS Running"}
