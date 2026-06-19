@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ============================================
echo   ARCHIVIEW v16 - проверка обновления
echo ============================================
echo.

set "REPO=%USERPROFILE%\Projects\chtenie-gorodskoy-pamyati"
echo [1] Git-проект:
echo     %REPO%
if exist "%REPO%\.git" (
    cd /d "%REPO%"
    echo     Последний коммит:
    git log -1 --oneline
) else (
    echo     НЕ НАЙДЕН .git
)
echo.

echo [2] Папка v16 на рабочем столе - файл версии:
if exist "%~dp0ARCHIVIEW_VERSION.txt" (
    type "%~dp0ARCHIVIEW_VERSION.txt"
) else (
    echo     ARCHIVIEW_VERSION.txt не найден в этой папке
)
echo.

echo [3] Дата archiview_gui.py в ЭТОЙ папке:
if exist "%~dp0archiview_gui.py" (
    dir /T:W "%~dp0archiview_gui.py" | findstr /i "archiview_gui.py"
) else (
    echo     archiview_gui.py не найден
)
echo.

echo [4] Дата archiview_gui.py в git-проекте:
if exist "%REPO%\tools\archiview-cv\archiview_gui.py" (
    dir /T:W "%REPO%\tools\archiview-cv\archiview_gui.py" | findstr /i "archiview_gui.py"
) else (
    echo     не найден
)
echo.

echo Если даты разные - запустите OBNOVIT_IZ_GITA.bat или setup из git.
echo В заголовке Archiview: v16 polygon edit
echo На вкладке 0 - Дом и сравнение, на 5 - кнопка localhost
echo.
pause
