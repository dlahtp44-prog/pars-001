from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app.db import query_inventory_stats  # 위에서 만든 함수

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/page/inventory-summary", response_class=HTMLResponse)
def inventory_summary_page(request: Request, year: int | None = None, month: int | None = None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    daily_data, brand_data, top_items = query_inventory_stats(year, month)

    # 차트용 데이터 가공
    labels = [r['day'] for r in daily_data]
    in_values = [r['in_qty'] for r in daily_data]
    out_values = [r['out_qty'] for r in daily_data]

    return templates.TemplateResponse("outbound_summary.html", {
        "request": request,
        "year": year,
        "month": month,
        "labels": labels,
        "in_values": in_values,
        "out_values": out_values,
        "brand_labels": [r['brand'] for r in brand_data],
        "brand_values": [r['total_qty'] for r in brand_data],
        "top_items": top_items,
        "rows": daily_data
    })
