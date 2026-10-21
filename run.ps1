Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  Starting Magic Fill Server..." -ForegroundColor Green
Write-Host "  Open in browser: http://127.0.0.1:8000/" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan

Set-Location "$PSScriptRoot\backend"
& ".\.venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload