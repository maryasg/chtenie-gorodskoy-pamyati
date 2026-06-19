@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ============================================
echo   ARCHIVIEW v16 - обновление из GitHub
echo ============================================
echo.

set "REPO=%USERPROFILE%\Projects\chtenie-gorodskoy-pamyati"
if not exist "%REPO%\.git" (
    echo Не найдена папка git-проекта:
    echo   %REPO%
    echo.
    echo Откройте cmd и выполните:
    echo   cd %REPO%
    echo   git pull
    echo   cd tools\archiview-cv
    echo   setup_v16_desktop.bat
    echo.
    pause
    exit /b 1
)

echo [1/3] git pull ...
cd /d "%REPO%"
git pull
if errorlevel 1 (
    echo.
    echo Ошибка git pull. Проверьте интернет и GitHub Desktop.
    pause
    exit /b 1
)

echo.
echo [2/3] Копирование файлов в папку v16 на рабочем столе ...
cd /d "%REPO%\tools\archiview-cv"
call setup_v16_desktop.bat
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo [3/3] Готово.
echo.
echo В папке v16 на рабочем столе:
echo   PROVERIT_OBNOVLENIE.bat  - проверить версию
echo   ZAPUSK_V16.bat           - запуск программы
echo.
pause
