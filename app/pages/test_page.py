from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/test", tags=["Page"], include_in_schema=False)

@router.get("/")
def test():
    return JSONResponse({"ok": True, "service": "PARS WMS"})
