@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "SRC=%~dp0"
set "SEARCH=%USERPROFILE%\Desktop\Cult Tech"
set "V16ROOT="

if not exist "%SEARCH%" (
    echo ERROR: Folder not found: %SEARCH%
    pause
    exit /b 1
)

for /f "delims=" %%I in ('dir /s /b /ad "%SEARCH%\archiview_cv_easy_v16_package" 2^>nul') do (
    set "V16ROOT=%%I"
    goto :found_v16
)

echo ERROR: archiview_cv_easy_v16_package not found.
echo First run: setup_v16_desktop.bat
pause
exit /b 1

:found_v16
echo Sync v16 code to:
echo   %V16ROOT%
echo.

set FILES=install_windows.bat requirements_archiview.txt run_gui_windows.bat run_gui_v15.bat run_gui_v16.bat copy_to_website.bat copy_to_website.ps1 sync_to_v15_desktop.ps1 sync_to_v15_desktop.bat sync_to_v16_desktop.ps1 sync_to_v16_desktop.bat bootstrap_v16_desktop.ps1 bootstrap_v16_desktop.bat setup_v16_desktop.ps1 setup_v16_desktop.bat update_website_registry.ps1 export_facade_project.ps1 export_moscow001_from_v15.ps1 restore_markup_from_website.ps1 restore_markup_from_website.bat website_buildings.json README_v16_ru.md archiview_gui.py archiview_project_model.py archiview_project_ui.py archiview_house_db.py archiview_cv.py

for %%F in (%FILES%) do (
    if exist "%SRC%%%F" (
        copy /Y "%SRC%%%F" "%V16ROOT%\" >nul
        echo OK: %%F
    ) else (
        echo SKIP: %%F
    )
)

copy /Y "%SRC%run_gui_v16.bat" "%V16ROOT%\run_gui_windows.bat" >nul
echo OK: run_gui_windows.bat ^(v16^)
copy /Y "%SRC%run_gui_v16.bat" "%V16ROOT%\ZAPUSK_V16.bat" >nul
echo OK: ZAPUSK_V16.bat
echo v16 polygon edit> "%V16ROOT%\ARCHIVIEW_VERSION.txt"
echo OK: ARCHIVIEW_VERSION.txt

echo.
echo ============================================
echo GOTO THIS FOLDER:
echo %V16ROOT%
echo Run: ZAPUSK_V16.bat
echo Title must say: v16 polygon edit
echo ============================================
echo.
pause
