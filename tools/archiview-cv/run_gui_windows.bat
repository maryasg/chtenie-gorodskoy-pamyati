@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if not exist "archiview_gui.py" (
    echo ERROR: archiview_gui.py not found in:
    echo   %~dp0
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" archiview_gui.py
    if errorlevel 1 goto failed
    goto end
)

echo .venv not found. Trying system Python...
echo If Archiview does not start, run install_windows.bat first.
echo.

where py >nul 2>nul
if not errorlevel 1 (
    py -3 archiview_gui.py
    if errorlevel 1 goto failed
    goto end
)

python archiview_gui.py
if errorlevel 1 goto failed
goto end

:failed
echo.
echo Archiview stopped with an error (see message above).
echo Fix: run install_windows.bat in this folder, then try again.
pause
exit /b 1

:end
pause
