@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ===============================================
echo Archiview CV - установка библиотек Windows
echo ===============================================
echo.

set "PY_CMD="
set "PY_LABEL="

if exist "%~dp0.venv\Scripts\python.exe" (
    for /f "usebackq delims=" %%P in (`"%~dp0.venv\Scripts\python.exe" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul`) do set "VENV_VER=%%P"
    if defined VENV_VER (
        echo Найден старый .venv с Python !VENV_VER!
        for /f "tokens=1,2 delims=." %%a in ("!VENV_VER!") do (
            if "%%b" geq "14" (
                echo Python 3.14+ не подходит для NumPy/OpenCV - удаляем .venv...
                rmdir /s /q "%~dp0.venv" 2>nul
            )
        )
    )
)

if exist "%~dp0.venv\Scripts\python.exe" (
  goto use_existing_venv
)

echo Ищем Python 3.12 или 3.11 ^(не 3.14!^)...
where py >nul 2>nul
if not errorlevel 1 (
    for %%V in (3.12 3.11 3.13 3.10) do (
        py -%%V -c "import sys" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD=py -%%V"
            set "PY_LABEL=%%V"
            goto found_python
        )
    )
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info < (3, 14) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=py -3"
        set "PY_LABEL=default py -3"
        goto found_python
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info < (3, 14) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=python"
        set "PY_LABEL=python"
        goto found_python
    )
)

echo.
echo ===============================================
echo   ОШИБКА: нужен Python 3.10 - 3.13
echo ===============================================
echo.
echo Сейчас у вас, похоже, только Python 3.14 ^(Chocolatey^).
echo NumPy и OpenCV с ним пока не работают.
echo.
echo Скачайте Python 3.12:
echo   https://www.python.org/downloads/release/python-31210/
echo.
echo При установке отметьте:
echo   [x] Add python.exe to PATH
echo.
echo Потом снова запустите install_windows.bat
echo.
pause
exit /b 1

:found_python
echo Используем Python: !PY_LABEL!
echo.

echo Создаём виртуальное окружение .venv ...
!PY_CMD! -m venv .venv
if errorlevel 1 (
    echo Не удалось создать .venv.
    pause
    exit /b 1
)
goto venv_ready

:use_existing_venv
echo Используем существующий .venv
echo.

:venv_ready
if not exist ".venv\Scripts\python.exe" (
    echo .venv\Scripts\python.exe не найден.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info < (3, 14) else 1)"
if errorlevel 1 (
    echo.
    echo ОШИБКА: в .venv Python 3.14+. Удалите папку .venv и запустите снова.
    pause
    exit /b 1
)

echo.
echo Обновляем pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Ошибка pip.
    pause
    exit /b 1
)

echo.
echo Ставим OpenCV, NumPy, Pillow...
".venv\Scripts\python.exe" -m pip install -r requirements_archiview.txt
if errorlevel 1 (
    echo Ошибка установки библиотек. Проверьте интернет.
    pause
    exit /b 1
)

echo.
echo Проверка NumPy и OpenCV...
".venv\Scripts\python.exe" -c "import numpy; import cv2; print('OK: numpy', numpy.__version__, 'opencv', cv2.__version__)"
if errorlevel 1 (
    echo.
    echo Проверка не прошла. Удалите папку .venv и запустите install_windows.bat снова.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   ГОТОВО
echo ===============================================
echo.
echo Запуск: ZAPUSK_V16.bat
echo.
pause
