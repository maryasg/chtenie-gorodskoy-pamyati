# One-time setup + update Archiview v16 on Desktop (run from tools\archiview-cv)
$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot

Write-Host ''
Write-Host '=== Archiview v16 setup ===' -ForegroundColor Green
Write-Host ''

& (Join-Path $Here 'bootstrap_v16_desktop.ps1')
& (Join-Path $Here 'sync_to_v16_desktop.ps1')

$v16 = Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter 'archiview_cv_easy_v16_package' -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $v16) {
    throw 'archiview_cv_easy_v16_package not found after setup'
}

$versionFile = Join-Path $v16.FullName 'ARCHIVIEW_VERSION.txt'
Set-Content -LiteralPath $versionFile -Value 'v16 polygon edit + stable site links' -Encoding UTF8

$zapusk = Join-Path $v16.FullName 'ZAPUSK_V16.bat'
Copy-Item -LiteralPath (Join-Path $Here 'run_gui_v16.bat') -Destination $zapusk -Force

if (-not (Test-Path -LiteralPath (Join-Path $v16.FullName '.venv\Scripts\python.exe'))) {
    Write-Host ''
    Write-Host 'Next: open v16 folder and run install_windows.bat (once)' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host 'V16 FOLDER (run run_gui_windows.bat HERE):' -ForegroundColor Cyan
Write-Host $v16.FullName -ForegroundColor White
Write-Host 'Or double-click: ZAPUSK_V16.bat' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Window title must say: v16 polygon edit' -ForegroundColor Green
Write-Host 'NOT v15 — if you see v15, you opened the wrong folder.' -ForegroundColor Yellow

Start-Process explorer.exe $v16.FullName
