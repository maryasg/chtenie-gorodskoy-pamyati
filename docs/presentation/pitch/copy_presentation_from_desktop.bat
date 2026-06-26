@echo off
chcp 65001 >nul
setlocal

set "SRC=C:\Users\Marusia\Desktop\Cult Tech\!Проект Память стен\Презентация для питчинга\!Презентация_Читать_стены.pdf"
set "DST=%~dp0Презентация_Читать_стены.pdf"

if not exist "%SRC%" (
  echo Файл не найден:
  echo %SRC%
  echo.
  echo Проверьте путь на рабочем столе и запустите снова.
  exit /b 1
)

copy /Y "%SRC%" "%DST%"
if errorlevel 1 (
  echo Ошибка копирования.
  exit /b 1
)

echo Готово: %DST%
echo Дальше в GitHub Desktop: Commit + Push
endlocal
