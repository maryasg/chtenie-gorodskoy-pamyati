# v16 отложена — этот скрипт обновляет ту же папку, что и sync_to_v15_desktop.ps1
Write-Host 'Note: v16 is deferred; syncing stable v15 build.' -ForegroundColor Yellow
& (Join-Path $PSScriptRoot 'sync_to_v15_desktop.ps1') @args
