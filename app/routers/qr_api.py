from fastapi import APIRouter, Response
from app.core.qr_generator import generate_qr_label

router = APIRouter(prefix="/qr", tags=["QR"])


@router.get("/label")
def qr_label(
    item_code: str,
    warehouse: str,
    location: str,
    lot_no: str,
    qty: float,
):
    pdf_path = generate_qr_label(item_code, warehouse, location, lot_no, qty)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_path}"}
    )

