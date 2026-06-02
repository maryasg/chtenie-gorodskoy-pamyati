@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ===============================================
echo Archiview CV v10 installer for Windows
echo ===============================================
echo.

echo Checking Python...
where py >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto found_python
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=python"
    goto found_python
)

echo Python was not found.
echo Install Python 3 from python.org and enable Add python.exe to PATH.
pause
exit /b 1

:found_python
echo Using Python command: %PY_CMD%
echo.

echo Creating virtual environment .venv ...
%PY_CMD% -m venv .venv
if errorlevel 1 (
    echo Failed to create .venv.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo .venv\Scripts\python.exe was not found after creation.
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

echo.
echo Installing OpenCV, NumPy and Pillow...
".venv\Scripts\python.exe" -m pip install -r requirements_archiview.txt
if errorlevel 1 (
    echo Failed to install OpenCV, NumPy and Pillow.
    echo Check internet connection and try again.
    pause
    exit /b 1
)

echo.
echo Done. Now run: run_gui_windows.bat
echo.
pause
