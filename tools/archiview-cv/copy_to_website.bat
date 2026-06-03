@echo off
setlocal DisableDelayedExpansion
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0copy_to_website.ps1"
