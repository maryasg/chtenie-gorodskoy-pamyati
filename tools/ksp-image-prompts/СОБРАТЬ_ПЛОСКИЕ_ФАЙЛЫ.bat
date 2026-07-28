@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

set MONTH=%~1
if "%MONTH%"=="" set MONTH=июнь

set ART=%USERPROFILE%\Projects\maryasg-articles_KorolevSP
set SITE=%USERPROFILE%\Projects\chtenie-gorodskoy-pamyati
set SRC=%SITE%\tools\ksp-image-prompts

echo.
echo ========================================
echo   Плоские файлы за месяц: %MONTH%
echo ========================================
echo.

if not exist "%ART%" (
    echo ОШИБКА: нет папки статей:
    echo   %ART%
    pause
    exit /b 1
)

if not exist "%SRC%\pack_month.py" (
    echo ОШИБКА: нет скриптов в сайте. Сначала:
    echo   cd /d "%SITE%"
    echo   git pull
    pause
    exit /b 1
)

echo [1/4] Копирую свежие скрипты...
copy /Y "%SRC%\pack_month.py" "%ART%\" >nul
copy /Y "%SRC%\pack_month.bat" "%ART%\" >nul
copy /Y "%SRC%\generate.py" "%ART%\" >nul
copy /Y "%SRC%\docx_export.py" "%ART%\" >nul
copy /Y "%SRC%\export_docx.py" "%ART%\" >nul
copy /Y "%SRC%\export_docx.bat" "%ART%\" >nul
echo       OK

cd /d "%ART%"

if exist .venv\Scripts\python.exe (
    set PY=.venv\Scripts\python.exe
) else (
    set PY=python
)

echo [2/4] Python:
%PY% --version
if errorlevel 1 (
    echo ОШИБКА: Python не найден. Создайте venv:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist content_plan\%MONTH%.json (
    echo ОШИБКА: нет content_plan\%MONTH%.json
    pause
    exit /b 1
)

set COUNT=0
if exist output\%MONTH% (
    for /d %%D in (output\%MONTH%\0*) do (
        if exist "%%D\vk.md" if exist "%%D\telegram.md" set /a COUNT+=1
    )
)
echo [3/4] Готовых статей ^(с vk.md и telegram.md^) в output\%MONTH%: !COUNT!

if !COUNT!==0 (
    echo.
    echo Статей еще нет. Нужна генерация ^(нужен ключ в .env^).
    echo.
    if not exist .env (
        echo ОШИБКА: нет файла .env с ключом API
        echo   copy .env.example .env
        pause
        exit /b 1
    )
    echo Запускаю: generate.py --plan content_plan\%MONTH%.json --skip-images
    echo.
    %PY% generate.py --plan content_plan\%MONTH%.json --skip-images
    if errorlevel 1 (
        echo.
        echo Генерация не удалась. Проверьте .env и интернет.
        pause
        exit /b 1
    )
)

echo.
echo [4/4] Собираю плоские файлы...
%PY% pack_month.py %MONTH%
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo [5/5] Собираю Word-файлы в папку месяца...
%PY% export_docx.py --filter-month %MONTH%
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ГОТОВО: %ART%\output\%MONTH%
echo   Ищите: статья01_%MONTH%_2026_ВК_....docx
echo          статья01_%MONTH%_2026_ТГМАКС_....docx
echo ========================================
explorer "%ART%\output\%MONTH%"
pause
