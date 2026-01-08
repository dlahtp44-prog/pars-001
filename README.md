# PARS WMS v1.6-stable

## Start (local)
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Deploy (Railway/Render)
Start Command(권장): uvicorn app.main:app --host 0.0.0.0 --port 8080
`uvicorn app.main:app --host 0.0.0.0 --port 8080`

DB는 최초 실행 시 자동 생성됩니다.


※ Railway에서 Custom Start Command에 `$PORT` 를 그대로 넣으면 문자로 전달되어 실패할 수 있습니다. 위 권장 Start Command처럼 **숫자 포트(8080)** 로 지정하거나, Custom Start Command를 비워 Dockerfile CMD를 사용하세요.
