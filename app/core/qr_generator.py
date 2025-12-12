
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
import os
from datetime import datetime


def generate_qr_label(item_code, warehouse, location, lot_no, qty):
    """
    70×40 mm QR 라벨 PDF 생성
    """
    label_width = 70 * mm
    label_height = 40 * mm

    # 출력 파일 경로
    output_path = f"qr_label_{item_code}_{lot_no}.pdf"

    # QR 텍스트 (기존 포맷 유지)
    qr_text = f"ITEM={item_code};WH={warehouse};LOC={location};LOT={lot_no};QTY={qty}"

    # PDF 생성
    c = canvas.Canvas(output_path, pagesize=(label_width, label_height))

    # QR 이미지 생성
    qr_img = qrcode.make(qr_text)
    qr_path = "temp_qr.png"
    qr_img.save(qr_path)

    # QR 크기 (28mm)
    qr_px = 28 * mm

    c.drawImage(qr_path, 2 * mm, label_height - qr_px - 2 * mm, qr_px, qr_px)

    # 텍스트 출력
    c.setFont("Helvetica-Bold", 8)
    c.drawString(35 * mm, label_height - 10 * mm, f"ITEM: {item_code}")
    c.drawString(35 * mm, label_height - 16 * mm, f"LOT: {lot_no}")
    c.drawString(35 * mm, label_height - 22 * mm, f"WH: {warehouse}")
    c.drawString(35 * mm, label_height - 28 * mm, f"LOC: {location}")
    c.drawString(35 * mm, label_height - 34 * mm, f"QTY: {qty}")

    c.save()

    # 임시 QR 이미지 삭제
    if os.path.exists(qr_path):
        os.remove(qr_path)

    return output_path
