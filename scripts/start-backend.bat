@echo off
cd /d "%~dp0\..\backend"
if exist .venv\Scripts\python.exe (
    echo Starting FastAPI Backend on port 8000...
    .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
) else (
    echo [ERROR] Virtual environment .venv not found.
    echo Please run scripts\setup-windows.bat first.
    pause
)
