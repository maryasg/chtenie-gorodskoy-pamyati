@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe pack_month.py %*
) else (
    python pack_month.py %*
)
if errorlevel 1 pause
