@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo Обновление файлов v15 из git...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_to_v15_desktop.ps1"
if errorlevel 1 (
    echo.
    echo ОШИБКА при копировании файлов v15.
    pause
    exit /b 1
)

pause
