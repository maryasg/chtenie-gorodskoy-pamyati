@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set ARCHIVIEW_APP_VERSION=16

echo.
echo ============================================
echo   ARCHIVIEW CV v16
echo   Papka: %~dp0
echo ============================================
echo.
echo Esli v zagolovke okna "v15" - vy v ne tot papke!
echo Nuzhna papka: archiview_cv_easy_v16_package
echo.

if not exist "archiview_gui.py" (
    echo ERROR: archiview_gui.py not found in:
    echo   %~dp0
    pause
    exit /b 1
)

findstr /C:"class AppV16" archiview_gui.py >nul 2>&1
if errorlevel 1 (
    echo WARNING: staryj archiview_gui.py bez v16. Zapustite sync_to_v16_desktop.ps1
    pause
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
echo Archiview v16 stopped with an error (see message above).
echo Fix: run install_windows.bat in this folder, then try again.
pause
exit /b 1

:end
pause
