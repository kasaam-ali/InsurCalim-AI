@echo off
REM ============================================================================
REM  InsurCalim AI - stop all services
REM  Stops the database container and the API / dashboard / landing dev servers.
REM  (Docker Desktop itself is left running - close it from the tray if needed.)
REM ============================================================================

setlocal
cd /d "%~dp0"

echo Stopping the database container...
docker compose -f infra/docker-compose.yml stop db

echo Stopping the API backend (port 8000)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :8000') do taskkill /f /pid %%p >nul 2>&1

echo Stopping the React dashboard (port 5174)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :5174') do taskkill /f /pid %%p >nul 2>&1

echo Stopping Streamlit (port 8501)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :8501') do taskkill /f /pid %%p >nul 2>&1

echo Stopping the landing dev server (port 5173)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr LISTENING ^| findstr :5173') do taskkill /f /pid %%p >nul 2>&1

echo.
echo Done. All app services stopped.
echo (Docker Desktop is still running - you can quit it from the system tray.)
echo.
pause
endlocal
