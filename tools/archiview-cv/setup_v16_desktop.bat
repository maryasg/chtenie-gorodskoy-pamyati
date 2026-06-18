@echo off
cd /d "%~dp0"

echo.
echo ============================================
echo   ARCHIVIEW v16 - setup ^(cmd, no PowerShell^)
echo ============================================
echo.

call "%~dp0bootstrap_v16_desktop.bat"
if errorlevel 1 exit /b 1

call "%~dp0sync_to_v16_desktop.bat"
if errorlevel 1 exit /b 1

echo.
echo Done. Open folder archiview_cv_easy_v16_package on Desktop.
echo Run install_windows.bat once, then ZAPUSK_V16.bat
echo.
pause
