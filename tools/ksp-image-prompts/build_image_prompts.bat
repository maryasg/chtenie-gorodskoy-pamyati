@echo off
chcp 65001 >nul
cd /d "%~dp0"
python build_image_prompts.py %*
if errorlevel 1 pause
