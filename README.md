# PARS WMS (운영 기준 전체 교체본)

이 ZIP은 **PARS WMS를 바로 실행/배포할 수 있도록 정리한 운영 기준 전체 교체본**입니다.

## 1) 로컬 실행

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

- 접속: `http://localhost:8000`
- 정적 파일: `/static/*`

## 2) Docker 실행

```bash
docker build -t pars-wms .
docker run --rm -p 8080:8080 -e PORT=8080 pars-wms
```

## 3) 데이터(DB)

- 기본 DB 파일: `app/data/wms.db`
- 앱 시작 시 `init_db()`에서 필요한 테이블을 생성합니다.
- 운영 환경에서는 DB 파일을 별도 볼륨/백업 정책으로 관리하는 것을 권장합니다.

## 4) 주요 화면

- PC 홈: `/`
- 로그인: `/page/login`
- 입고: `/page/inbound`
- 출고: `/page/outbound`
- 출고 요약: `/page/outbound-summary`
- 이동: `/page/move`
- 재고: `/page/inventory`
- 이력: `/page/history`
- 엑셀 센터: `/page/excel`
- 달력(PC): `/page/calendar`

### 모바일

- 모바일 홈: `/m`
- QR 스캔: `/m/qr`
- QR 재고조회: `/m/qr-inventory`
- 모바일 이동: `/m/move`
- 모바일 CS: `/m/cs`
- 달력(모바일): `/m/calendar`

## 5) 환경변수

- `PORT` : 서비스 포트 (기본 8080 또는 uvicorn 옵션)
- `ENV` : `production` / `development` (기본 `development`)
- `RESET_DB` : `1`이면 **개발환경에서만** inventory/history 초기화

