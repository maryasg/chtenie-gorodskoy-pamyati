@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" archiview_gui.py
    goto end
)

echo .venv not found. Trying system Python...
where py >nul 2>nul
if not errorlevel 1 (
    py -3 archiview_gui.py
    goto end
)

python archiview_gui.py

:end
pause
