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

if exist "%RESULT%\project_v8.json" (
    powershell -NoProfile -Command "$p=Get-Content '%RESULT%\project_v8.json' -Raw | ConvertFrom-Json; @{H_rect_to_modern=$p.H_rect_to_modern} | ConvertTo-Json -Depth 5 | Set-Content '%WEB%\facade-project.json' -Encoding UTF8"
    echo OK: facade-project.json
)

echo.
echo Дальше: GitHub Desktop - Commit - Push для репозитория chtenie-gorodskoy-pamyati
pause
