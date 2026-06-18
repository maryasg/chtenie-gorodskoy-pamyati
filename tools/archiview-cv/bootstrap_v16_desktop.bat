@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo [1/2] Создание папки v16 на рабочем столе...
echo       Копируем из v15 (папки с русскими буквами в пути).
echo       Вы запускаете cmd — копирование идёт через встроенный Windows-скрипт.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap_v16_desktop.ps1"
if errorlevel 1 (
    echo.
    echo ОШИБКА при создании папки v16.
    echo Проверьте, что папка archiview_cv_easy_v15_package есть на рабочем столе.
    if not defined SETUP_V16_NO_PAUSE pause
    exit /b 1
)

echo OK: папка v16 готова.
if not defined SETUP_V16_NO_PAUSE pause
