from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import query_outbound_summary

router = APIRouter(prefix="/page/outbound-summary", tags=["출고통계"])
templates = Jinja2Templates(directory="templates")

@router.get("")
def outbound_summary_page(request: Request, year: int, month: int):
    data = query_outbound_summary(year, month)
    return templates.TemplateResponse(
        "outbound_summary.html",
        {
            "request": request,
            "data": data,
            "year": year,
            "month": month,
        }
    )
