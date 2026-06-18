@echo off
cd /d "%~dp0"

if "%~1"=="" (
    echo.
    echo Usage: restore_markup_from_website.bat MOSCOW_003
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0restore_markup_from_website.ps1" -CardId %1
if errorlevel 1 (
    echo.
    echo ERROR: restore failed
    pause
    exit /b 1
)

echo.
echo OK: markup restored for %1
pause
