from __future__ import annotations

import re
from datetime import datetime, date
from typing import Dict, List

from fastapi import APIRouter, Form, HTTPException

from app.db import get_db

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _ensure_tables():
    """
    db.py 수정 없이도 동작하도록 API 호출 시 테이블 보장
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS calendar_memo (
                memo_date TEXT NOT NULL,
                line_no   INTEGER NOT NULL,
                content   TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (memo_date, line_no)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_calendar_memo_date ON calendar_memo (memo_date)"
        )
        conn.commit()
    finally:
        conn.close()


def _validate_date_str(s: str) -> str:
    s = (s or "").strip()
    if not _DATE_RE.match(s):
        raise HTTPException(status_code=400, detail="date 형식은 YYYY-MM-DD 입니다.")
    # 실제 날짜 유효성
    try:
        date.fromisoformat(s)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 날짜입니다.")
    return s


def _norm_line(s: str) -> str:
    s = (s or "").strip()
    # 20자 제한 (서버 강제)
    if len(s) > 20:
        s = s[:20]
    return s


def _lines_from_form(line1: str, line2: str, line3: str, line4: str) -> List[str]:
    return [_norm_line(line1), _norm_line(line2), _norm_line(line3), _norm_line(line4)]


@router.get("/day")
def get_day(date: str):
    _ensure_tables()
    d = _validate_date_str(date)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT line_no, content
            FROM calendar_memo
            WHERE memo_date=?
            ORDER BY line_no ASC
            """,
            (d,),
        )
        rows = cur.fetchall()
        lines = ["", "", "", ""]
        for r in rows:
            idx = int(r["line_no"]) - 1
            if 0 <= idx < 4:
                lines[idx] = r["content"] or ""
        return {"ok": True, "date": d, "lines": lines}
    finally:
        conn.close()


@router.get("/month")
def get_month(year: int, month: int):
    """
    반환:
    {
      ok: true,
      items: { "YYYY-MM-DD": ["", "", "", ""] }
    }
    """
    _ensure_tables()
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="year 범위 오류")
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month 범위 오류")

    # 월 범위 계산
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT memo_date, line_no, content
            FROM calendar_memo
            WHERE memo_date >= ? AND memo_date < ?
            ORDER BY memo_date ASC, line_no ASC
            """,
            (start.isoformat(), end.isoformat()),
        )
        items: Dict[str, List[str]] = {}
        for r in cur.fetchall():
            d = r["memo_date"]
            if d not in items:
                items[d] = ["", "", "", ""]
            idx = int(r["line_no"]) - 1
            if 0 <= idx < 4:
                items[d][idx] = r["content"] or ""
        return {"ok": True, "year": year, "month": month, "items": items}
    finally:
        conn.close()


@router.post("/save")
def save_day(
    date: str = Form(...),
    line1: str = Form(""),
    line2: str = Form(""),
    line3: str = Form(""),
    line4: str = Form(""),
    operator: str = Form(""),
):
    _ensure_tables()
    d = _validate_date_str(date)
    lines = _lines_from_form(line1, line2, line3, line4)
    op = (operator or "").strip()
    now = _now()

    conn = get_db()
    try:
        cur = conn.cursor()

        # 1~4 라인 UPSERT
        for i, content in enumerate(lines, start=1):
            cur.execute(
                """
                INSERT INTO calendar_memo (memo_date, line_no, content, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(memo_date, line_no) DO UPDATE SET
                    content=excluded.content,
                    updated_at=excluded.updated_at,
                    updated_by=excluded.updated_by
                """,
                (d, i, content, now, op),
            )

        conn.commit()
        return {"ok": True, "date": d, "lines": lines}
    finally:
        conn.close()


@router.post("/delete")
def delete_day(
    date: str = Form(...),
):
    _ensure_tables()
    d = _validate_date_str(date)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM calendar_memo WHERE memo_date=?", (d,))
        conn.commit()
        return {"ok": True, "date": d}
    finally:
        conn.close()
