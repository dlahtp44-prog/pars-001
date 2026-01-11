# PARS WMS - 월간 달력(PC+모바일) 기능 패치(단독 ZIP)

이 ZIP은 **기존 기능을 삭제/수정하지 않고**, 달력 기능 파일만 **추가**로 제공합니다.

## 1) ZIP 풀고, 프로젝트 루트에 그대로 복사
`app/` 폴더가 이미 있는 곳(프로젝트 루트)에 그대로 덮어쓰기(추가) 하세요.

추가되는 파일:
- `app/pages/calendar.py`
- `app/pages/mobile_calendar.py`
- `app/routers/api_calendar.py`
- `app/templates/calendar.html`
- `app/templates/mobile/calendar.html`
- `app/static/calendar.css`, `app/static/calendar.js`
- `app/static/mobile_calendar.css`, `app/static/mobile_calendar.js`

## 2) main.py에 라우터 4줄만 추가 (필수)
아래를 **PC PAGES 섹션** / **MOBILE 섹션** / **API 섹션**에 각각 추가하세요.

### PC PAGES
```python
from app.pages.calendar import router as calendar_page_router
app.include_router(calendar_page_router)
```

### MOBILE
```python
from app.pages.mobile_calendar import router as mobile_calendar_router
app.include_router(mobile_calendar_router)
```

### API
```python
from app.routers.api_calendar import router as api_calendar_router
app.include_router(api_calendar_router)
```

## 3) 접속 URL
- PC: `/page/calendar`
- 모바일: `/m/calendar`

## 4) 데이터 저장(DB)
- 기존 `app.db.get_db()`를 사용합니다.
- **db.py 수정 없이** API가 호출될 때 자동으로 `calendar_memo` 테이블을 `CREATE TABLE IF NOT EXISTS`로 생성합니다.

## 5) 요구사항 반영
- 월간 달력 + 날짜 선택 후 메모 입력/저장/수정/삭제
- 일자당 최대 4줄, 1줄 20자 제한(서버에서 강제)
- 20자 써도 칸 높이 고정(잘림/… 처리)
- 메모는 달력 칸에 항상 표시(숨김 없음)
- 월 넘어가도 전달 메모 유지(DB 저장)
