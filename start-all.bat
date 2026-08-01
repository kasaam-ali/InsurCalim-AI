@echo off
REM ============================================================================
REM  InsurClaim AI - one-click launcher
REM  Starts everything needed for the demo:
REM    1) Docker Desktop (engine for the database)
REM    2) PostgreSQL database (docker compose)
REM    3) API backend (Starlette)           (http://localhost:8000)
REM    4) React investigator dashboard      (http://localhost:5174)
REM    5) Streamlit dashboard (classic)     (http://localhost:8501)
REM    6) React landing page                (http://localhost:5173)
REM  Then opens the landing page in the default browser.
REM
REM  Just double-click this file. Leave the windows it opens running during
REM  the presentation. To stop everything, run  stop-all.bat  (or close them).
REM ============================================================================

setlocal
cd /d "%~dp0"

echo ============================================================
echo   InsurClaim AI - starting all services
echo ============================================================
echo.

REM --- 1) Docker Desktop -------------------------------------------------------
echo [1/4] Checking Docker...
docker info >nul 2>&1
if %errorlevel%==0 (
    echo       Docker is already running.
) else (
    echo       Starting Docker Desktop... please wait.
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo       Waiting for the Docker engine to come up...
    set /a tries=0
    :waitdocker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel%==0 goto dockerready
    set /a tries+=1
    if %tries% geq 40 (
        echo       ERROR: Docker did not start in time. Open Docker Desktop manually and re-run.
        pause
        exit /b 1
    )
    goto waitdocker
    :dockerready
    echo       Docker engine is ready.
)
echo.

REM --- 2) Database ------------------------------------------------------------
echo [2/4] Starting the PostgreSQL database...
docker compose -f infra/docker-compose.yml up -d db
echo       Waiting for the database to become healthy...
set /a dbtries=0
:waitdb
timeout /t 3 /nobreak >nul
for /f "delims=" %%i in ('docker compose -f infra/docker-compose.yml ps -q db 2^>nul') do set DBID=%%i
for /f "delims=" %%s in ('docker inspect --format "{{.State.Health.Status}}" %DBID% 2^>nul') do set DBHEALTH=%%s
echo       db health: %DBHEALTH%
if "%DBHEALTH%"=="healthy" goto dbready
set /a dbtries+=1
if %dbtries% geq 20 (
    echo       WARNING: database not healthy yet, continuing anyway...
    goto dbready
)
goto waitdb
:dbready
echo.

REM --- 3) API backend ---------------------------------------------------------
echo [3/6] Starting the API backend in a new window...
start "InsurClaim - API" cmd /k ".venv\Scripts\python.exe -m uvicorn api.main:app --port 8000"
echo.

REM --- 4) React investigator dashboard ----------------------------------------
echo [4/6] Starting the React investigator dashboard in a new window...
start "InsurClaim - Dashboard (React)" cmd /k "cd dashboard && npm run dev"
echo.

REM --- 5) Streamlit dashboard (classic view) ---------------------------------
echo [5/6] Starting the classic Streamlit dashboard in a new window...
start "InsurClaim - Dashboard (Streamlit)" cmd /k ".venv\Scripts\streamlit.exe run frontend/app.py --server.port 8501"
echo.

REM --- 6) Landing page --------------------------------------------------------
echo [6/6] Starting the landing page in a new window...
start "InsurClaim - Landing" cmd /k "cd landing && npm run dev"
echo.

echo       Giving the servers a few seconds to boot...
timeout /t 10 /nobreak >nul

echo.
echo ============================================================
echo   All services launched.
echo     Landing page      : http://localhost:5173
echo     Dashboard (React) : http://localhost:5174
echo     Dashboard (Streamlit) : http://localhost:8501
echo     API backend       : http://localhost:8000
echo     Login             : admin / insurclaim2026
echo ============================================================
echo   Opening the landing page in your browser...
start "" "http://localhost:5173"
echo.
echo   Keep the new windows (API + Dashboard + Streamlit + Landing) open during the demo.
echo   Close this window whenever you like.
echo.
pause
endlocal
