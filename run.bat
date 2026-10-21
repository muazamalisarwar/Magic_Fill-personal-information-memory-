@echo off
title Magic Fill Server
echo ====================================================
echo           Starting Magic Fill Server...
echo   Open in browser: http://127.0.0.1:8000/
echo ====================================================
cd /d "%~dp0backend"
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
pause
