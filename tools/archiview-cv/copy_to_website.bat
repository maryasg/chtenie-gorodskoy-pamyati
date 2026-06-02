@echo off
chcp 65001 >nul
setlocal
set "RESULT=%~dp0archiview_projects\20260520_190036\result"
set "WEB=c:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\public\explorer\MOSCOW_003"

if not exist "%WEB%" mkdir "%WEB%"

if exist "%RESULT%\07_marked_on_original_modern.png" (
    copy /Y "%RESULT%\07_marked_on_original_modern.png" "%WEB%\marked-facade.png"
    echo OK: marked-facade.png
) else (
    echo НЕТ: 07_marked_on_original_modern.png — сначала сохраните разметку в программе.
)

if exist "%RESULT%\08_marked_on_original_modern_labeled.png" (
    copy /Y "%RESULT%\08_marked_on_original_modern_labeled.png" "%WEB%\marked-facade-labeled.png"
    echo OK: marked-facade-labeled.png
)

if exist "%RESULT%\annotations\manual_annotations.json" (
    copy /Y "%RESULT%\annotations\manual_annotations.json" "%WEB%\annotations.json"
    echo OK: annotations.json
)

echo.
echo Дальше: GitHub Desktop - Commit - Push для репозитория chtenie-gorodskoy-pamyati
pause
