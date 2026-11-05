@echo off
cd /d "%~dp0..\backend"
call .venv\Scripts\activate
pytest -q
