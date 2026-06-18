@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo [2/2] Обновление файлов v16 из git...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_to_v16_desktop.ps1"
if errorlevel 1 (
    echo.
    echo ОШИБКА при копировании файлов.
    echo Сначала запустите setup_v16_desktop.bat целиком.
    if not defined SETUP_V16_NO_PAUSE pause
    exit /b 1
)

if not defined SETUP_V16_NO_PAUSE pause
