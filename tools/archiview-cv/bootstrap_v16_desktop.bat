@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "SEARCH=%USERPROFILE%\Desktop\Cult Tech"
set "V15ROOT="

if not exist "%SEARCH%" (
    echo ERROR: Folder not found: %SEARCH%
    pause
    exit /b 1
)

for /f "delims=" %%I in ('dir /s /b /ad "%SEARCH%\archiview_cv_easy_v15_package" 2^>nul') do (
    set "V15ROOT=%%I"
    goto :found_v15
)

echo ERROR: archiview_cv_easy_v15_package not found under Desktop\Cult Tech
pause
exit /b 1

:found_v15
for %%I in ("%V15ROOT%") do set "V16ROOT=%%~dpIarchiview_cv_easy_v16_package"

if exist "%V16ROOT%" (
    echo v16 folder already exists:
    echo   %V16ROOT%
    echo Run setup_v16_desktop.bat to update files.
    goto :end
)

echo Copy v15 -^> v16 without .venv ...
echo   from: %V15ROOT%
echo   to:   %V16ROOT%
echo.

robocopy "%V15ROOT%" "%V16ROOT%" /E /XD .venv /NFL /NDL /NJH /NJS /nc /ns /np
if errorlevel 8 (
    echo ERROR: copy failed
    pause
    exit /b 1
)

echo OK: v16 folder created.

:end
echo.
pause
