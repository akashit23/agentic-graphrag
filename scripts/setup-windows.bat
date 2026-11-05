@echo off
REM One-time setup for Windows. Run from the project root: scripts\setup-windows.bat
cd /d "%~dp0..\backend"
py -3.11 -m venv .venv || goto :err
call .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu || goto :err
pip install -r requirements.txt || goto :err
if not exist .env copy .env.example .env
python scripts\download_models.py || goto :err
cd /d "%~dp0..\frontend"
call npm install || goto :err
echo.
echo Setup finished. Now run:  ollama pull qwen2.5-coder:3b   (once)
echo Then start with scripts\start-backend.bat and scripts\start-frontend.bat
goto :eof
:err
echo Setup failed. See the message above and the Troubleshooting table in README.md
exit /b 1
