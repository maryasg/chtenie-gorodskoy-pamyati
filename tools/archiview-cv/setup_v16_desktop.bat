@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set "IN_GIT_REPO=0"
if exist "%~dp0..\..\.git" set "IN_GIT_REPO=1"
if exist "%~dp0..\..\..\.git" set "IN_GIT_REPO=1"

if exist "%~dp0ARCHIVIEW_VERSION.txt" if "%IN_GIT_REPO%"=="0" (
    echo.
    echo ============================================
    echo   ОШИБКА: неверная папка для setup
    echo ============================================
    echo.
    echo Вы запустили setup из папки v16 на Рабочем столе.
    echo Здесь нет git - обновление так не работает.
    echo.
    echo Правильно - один из вариантов:
    echo.
    echo   Вариант A - дважды щёлкните в папке v16 на рабочем столе:
    echo      OBNOVIT_IZ_GITA.bat
    echo.
    echo   Вариант B - или в cmd:
    echo      cd %USERPROFILE%\Projects\chtenie-gorodskoy-pamyati
    echo      git pull
    echo      cd tools\archiview-cv
    echo      setup_v16_desktop.bat
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ARCHIVIEW v16 - настройка
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
echo   рядом с v15, внутри Cult Tech\Проект Память стен\...
echo.
echo В этой папке v16:
echo   install_windows.bat   - один раз, если ещё не ставили
echo   ZAPUSK_V16.bat        - запуск программы
echo.
echo В заголовке окна должно быть: v16 polygon edit
echo ============================================
echo.
pause
