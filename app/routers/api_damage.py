from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.db import add_damage_history, list_damage_codes

router = APIRouter(prefix="/api/damage", tags=["CS/파손"])


@router.post("")
def create_damage(
    request: Request,
    occurred_at: str = Form(...),
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    damage_code_id: int = Form(...),
    detail: str = Form(""),
    deduct_inventory: bool = Form(False),
):
    try:
        add_damage_history(
            occurred_at=occurred_at,
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty=qty,
            damage_code_id=damage_code_id,
            detail=detail,
            deduct_inventory=deduct_inventory,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파손 등록 오류: {e}")

    return RedirectResponse(
        url="/damage",
        status_code=HTTP_303_SEE_OTHER,
    )


@router.get("/codes")
def get_damage_codes():
    return list_damage_codes()
