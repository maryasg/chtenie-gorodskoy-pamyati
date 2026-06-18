param(
    [string]$V16Root = ''
)

$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot

function Find-DesktopPackage([string]$FolderName) {
    $root = Join-Path $env:USERPROFILE 'Desktop\Cult Tech'
    if (-not (Test-Path -LiteralPath $root)) { return $null }
    return Get-ChildItem -LiteralPath $root -Recurse -Directory -Filter $FolderName -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

if (-not $V16Root) {
    $found = Find-DesktopPackage 'archiview_cv_easy_v16_package'
    if (-not $found) {
        throw @'
archiview_cv_easy_v16_package not found under Desktop\Cult Tech.

First time: run bootstrap_v16_desktop.ps1 (copies v15 folder to v16), then run this script again.
'@
    }
    $V16Root = $found.FullName
}

$files = @(
    'install_windows.bat',
    'requirements_archiview.txt',
    'run_gui_windows.bat',
    'run_gui_v15.bat',
    'run_gui_v16.bat',
    'copy_to_website.bat',
    'copy_to_website.ps1',
    'sync_to_v15_desktop.ps1',
    'sync_to_v16_desktop.ps1',
    'bootstrap_v16_desktop.ps1',
    'update_website_registry.ps1',
    'export_facade_project.ps1',
    'export_moscow001_from_v15.ps1',
    'restore_markup_from_website.ps1',
    'website_buildings.json',
    'README_v16_ru.md',
    'archiview_gui.py',
    'archiview_project_model.py',
    'archiview_project_ui.py',
    'archiview_house_db.py',
    'archiview_cv.py'
)

foreach ($name in $files) {
    $from = Join-Path $Src $name
    if (-not (Test-Path -LiteralPath $from)) {
        Write-Host "SKIP: $name"
        continue
    }
    $dest = Join-Path $V16Root $name
    Copy-Item -LiteralPath $from -Destination $dest -Force
    Write-Host "OK: $name"
}

$launcherV16 = Join-Path $Src 'run_gui_v16.bat'
$launcherDest = Join-Path $V16Root 'run_gui_windows.bat'
Copy-Item -LiteralPath $launcherV16 -Destination $launcherDest -Force
Write-Host 'OK: run_gui_windows.bat (v16 launcher)'

Write-Host ''
Write-Host "Synced Archiview v16 to: $V16Root"
Write-Host 'Run run_gui_windows.bat — title should contain v16 polygon edit.'
