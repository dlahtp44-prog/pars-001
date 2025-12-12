PARS WMS QR + 버튼 최종 패키지

1. 폴더 구조
   backend/  -> FastAPI 서버 (app.py, WMS.db 생성)
   frontend/ -> index.html (버튼 + QR UI)
   run_server.bat -> 더블클릭 시 서버 자동 실행

2. 실행 방법
   1) Python 3.11 + FastAPI + Uvicorn 설치 완료 상태에서
   2) run_server.bat 더블클릭
   3) 브라우저에서 index.html 열기
      - 방법 A: frontend/index.html 을 더블클릭 (파일 경로로 열기)
      - 방법 B: VSCode Live Server 등으로 열기

3. QR 포맷
   - 입고
     ITEM=FM028CRN;WH=ICHEON;LOC=D01-01;LOT=ORIGIN;QTY=10
     IN:ICHEON,D01-01,FM028CRN,LOT=ORIGIN,10

   - 출고
     ITEM=FM028CRN;WH=ICHEON;LOC=D01-02;LOT=A1;QTY=5
     OUT:ICHEON,D01-02,FM028CRN,LOT=A1,5

   - 이동
     ITEM=FM028CRN;LOT=ORIGIN;WHF=ICHEON;LOCF=D01-01;WHT=ICHEON;LOCT=D01-02;QTY=5
     MOVE:ICHEON,D01-01,ICHEON,D01-02,FM028CRN,LOT=ORIGIN,5

