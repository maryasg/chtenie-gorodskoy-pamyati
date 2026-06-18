@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ============================================
echo   ARCHIVIEW v16 - настройка (запуск из cmd)
echo ============================================
echo.

set SETUP_V16_NO_PAUSE=1
call "%~dp0bootstrap_v16_desktop.bat"
if errorlevel 1 exit /b 1

call "%~dp0sync_to_v16_desktop.bat"
if errorlevel 1 exit /b 1
set SETUP_V16_NO_PAUSE=

echo.
echo ============================================
echo   ГОТОВО
echo ============================================
echo.
echo Откройте на рабочем столе папку:
echo   archiview_cv_easy_v16_package
echo   (рядом с v15, внутри Cult Tech\Проект Память стен\...)
echo.
echo В этой папке v16:
echo   install_windows.bat   - один раз, если ещё не ставили
echo   ZAPUSK_V16.bat        - запуск программы
echo.
echo В заголовке окна должно быть: v16 polygon edit
echo ============================================
echo.
pause
