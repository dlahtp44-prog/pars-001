from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import re

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_LOC_RE = re.compile(r"^[A-Za-z0-9\-_/]+$")

def _validate_location(raw: str):
    loc = (raw or "").strip()
    if not loc:
        return None
    if any(x in loc for x in ["&", "?", "="]):
        return None
    if len(loc) > 60:
        return None
    if not _LOC_RE.match(loc):
        return None
    return loc


@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, location: str = "", warehouse: str = ""):
    warehouse = (warehouse or "").strip()
    from_location = _validate_location(location)

    if not from_location:
        return templates.TemplateResponse(
            "m/move_from.html",
            {
                "request": request,
                "from_location": "",
                "warehouse": warehouse,
                "msg": "로케이션 QR이 올바르지 않습니다.",
            },
        )

    return templates.TemplateResponse(
        "m/move_from.html",
        {
            "request": request,
            "from_location": from_location,
            "warehouse": warehouse,
            "msg": "",
        },
    )


@router.post("/from/submit")
def move_from_submit(
    request: Request,
    from_location: str = Form(...),
    warehouse: str = Form(""),
):
    fl = _validate_location(from_location)
    warehouse = (warehouse or "").strip()

    if not fl:
        return templates.TemplateResponse(
            "m/move_from.html",
            {
                "request": request,
                "from_location": "",
                "warehouse": warehouse,
                "msg": "로케이션 QR이 올바르지 않습니다.",
            },
        )

    return RedirectResponse(
        url=f"/m/move/select?from_location={fl}&warehouse={warehouse}",
        status_code=303,
    )
