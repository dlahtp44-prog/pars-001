@echo off
echo ==========================================
echo   PARS WMS SERVER START (Auto Detect)
echo ==========================================

cd /d %~dp0

REM -------------------------------
REM Python 실행 파일 자동 감지
REM -------------------------------

SET PY_EXEC=

where py >nul 2>nul
IF %ERRORLEVEL%==0 (
    SET PY_EXEC=py
)

if not defined PY_EXEC (
    where python >nul 2>nul
    IF %ERRORLEVEL%==0 (
        SET PY_EXEC=python
    )
)

if not defined PY_EXEC (
    where python3 >nul 2>nul
    IF %ERRORLEVEL%==0 (
        SET PY_EXEC=python3
    )
)

REM -------------------------------
REM Python 실행 파일 없을 때
REM -------------------------------

if not defined PY_EXEC (
    echo [ERROR] Python 실행 파일(py, python, python3)을 찾을 수 없습니다.
    echo Python을 설치 후, PATH에 등록해주세요.
    pause
    exit /b 1
)

echo Python 실행 감지됨: %PY_EXEC%

REM -------------------------------
REM FastAPI 서버 실행
REM -------------------------------

%PY_EXEC% -m uvicorn main:app --reload

pause
