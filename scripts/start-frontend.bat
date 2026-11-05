@echo off
cd /d "%~dp0\..\frontend"
if exist node_modules (
    echo Starting Vite Frontend on port 5173...
    npm run dev
) else (
    echo Installing frontend dependencies...
    call npm install
    npm run dev
)
