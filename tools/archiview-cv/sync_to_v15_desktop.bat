@echo off
cd /d "%~dp0"

set "SEARCH=%USERPROFILE%\Desktop\Cult Tech"
set "V15ROOT="

for /f "delims=" %%I in ('dir /s /b /ad "%SEARCH%\archiview_cv_easy_v15_package" 2^>nul') do (
    set "V15ROOT=%%I"
    goto :found
)
echo ERROR: v15 package not found
pause
exit /b 1

:found
echo Sync v15 to: %V15ROOT%
echo.

set FILES=install_windows.bat requirements_archiview.txt run_gui_windows.bat run_gui_v15.bat run_gui_v16.bat copy_to_website.bat sync_to_v15_desktop.bat sync_to_v16_desktop.bat setup_v16_desktop.bat archiview_gui.py archiview_project_model.py archiview_project_ui.py archiview_house_db.py archiview_cv.py website_buildings.json README_v15_ru.md restore_markup_from_website.ps1 restore_markup_from_website.bat

for %%F in (%FILES%) do (
    if exist "%~dp0%%F" copy /Y "%~dp0%%F" "%V15ROOT%\" >nul && echo OK: %%F
)

copy /Y "%~dp0run_gui_v15.bat" "%V15ROOT%\run_gui_windows.bat" >nul
echo OK: run_gui_windows.bat ^(v15^)
echo.
pause
