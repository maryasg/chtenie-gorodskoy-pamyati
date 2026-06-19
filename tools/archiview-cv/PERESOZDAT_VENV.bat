@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ===============================================
echo   Archiview - пересоздать .venv
echo ===============================================
echo.
echo Удаляем старую папку .venv ^(если была Python 3.14 - это исправит ошибку^)
echo.

if exist ".venv" (
    rmdir /s /q ".venv"
    echo Старая .venv удалена.
) else (
    echo Папки .venv не было.
)

echo.
call "%~dp0install_windows.bat"
