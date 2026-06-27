@echo off
chcp 65001 >nul
cd /d "%~dp0"
python export_docx.py %*
if errorlevel 1 pause
