@echo off
title Magic Fill - Dual Launcher
color 0B
cls
echo ======================================================================
echo             MAGIC FILL - ONE-CLICK SYSTEM LAUNCHER
echo ======================================================================
echo.
echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Magic Fill Backend [Port 8000]" cmd /k "cd /d "%~dp0backend" && if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Starting Astro Frontend on http://localhost:4321 ...
start "Magic Fill Frontend [Port 4321]" cmd /k "cd /d "%~dp0automark-v1.0.0" && npm run dev"

echo [3/3] Waiting 4 seconds for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening browser at http://localhost:4321/ ...
start http://localhost:4321/

echo.
echo ======================================================================
echo SUCCESS: Both Backend and Frontend are now running!
echo.
echo - Backend API & Docs : http://127.0.0.1:8000/docs
echo - Frontend Web App   : http://localhost:4321/
echo.
echo (Keep the opened terminal windows running. Close them to stop services.)
echo ======================================================================
echo.
pause
