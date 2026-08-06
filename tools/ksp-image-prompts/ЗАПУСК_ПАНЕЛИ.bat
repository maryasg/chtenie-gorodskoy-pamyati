@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Панель генератора статей КСП
echo ============================================
echo.
echo Сейчас откроется окно с кнопками по шагам:
echo   1. Темы на месяц
echo   2. Проверка KupiAPI
echo   3. Генерация статей
echo   4. Промпты для картинок
echo   5. Плоские Word-файлы
echo   6. Готовые ручные статьи
echo.
echo Подсказка в браузере: ПАНЕЛЬ_РАБОТЫ.html
echo.

if exist "ПАНЕЛЬ_РАБОТЫ.html" (
    start "" "ПАНЕЛЬ_РАБОТЫ.html"
)

set PY=
if exist "%USERPROFILE%\Projects\maryasg-articles_KorolevSP\.venv\Scripts\python.exe" (
    set "PY=%USERPROFILE%\Projects\maryasg-articles_KorolevSP\.venv\Scripts\python.exe"
)
if exist ".venv\Scripts\python.exe" (
    set "PY=%CD%\.venv\Scripts\python.exe"
)
if "%PY%"=="" (
    where py >nul 2>&1 && set PY=py -3
)
if "%PY%"=="" (
    where python >nul 2>&1 && set PY=python
)

if "%PY%"=="" (
    echo Python не найден. Установите Python 3.10-3.13.
    echo HTML-подсказка уже открыта в браузере.
    pause
    exit /b 1
)

echo Запускаю окно с кнопками...
%PY% "%~dp0workflow_gui.py"
if errorlevel 1 (
    echo.
    echo Не удалось запустить панель. Откройте ПАНЕЛЬ_РАБОТЫ.html вручную.
    pause
)
