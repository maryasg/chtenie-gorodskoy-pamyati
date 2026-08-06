@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe test_kupiapi.py
) else (
    python test_kupiapi.py
)
pause
