param(
    [string]$V15Root = ''
)

$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot

if (-not $V15Root) {
    $patterns = @('archiview_cv_easy_v15_package')
    $found = $null
    foreach ($pattern in $patterns) {
        $hits = Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter $pattern -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($hits) {
            $found = $hits
            break
        }
    }
    if (-not $found) {
        throw 'archiview_cv_easy_v15_package not found under Desktop\Cult Tech'
    }
    $V15Root = $found.FullName
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
    'sync_to_v15_desktop.bat',
    'sync_to_v16_desktop.ps1',
    'sync_to_v16_desktop.bat',
    'bootstrap_v16_desktop.ps1',
    'bootstrap_v16_desktop.bat',
    'setup_v16_desktop.bat',
    'update_website_registry.ps1',
    'export_facade_project.ps1',
    'export_moscow001_from_v15.ps1',
    'restore_markup_from_website.ps1',
    'restore_markup_from_website.bat',
    'website_buildings.json',
    'README_v15_ru.md',
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
    Copy-Item -LiteralPath $from -Destination (Join-Path $V15Root $name) -Force
    Write-Host "OK: $name"
}

$launcherV15 = Join-Path $Src 'run_gui_v15.bat'
$launcherDest = Join-Path $V15Root 'run_gui_windows.bat'
Copy-Item -LiteralPath $launcherV15 -Destination $launcherDest -Force
Write-Host 'OK: run_gui_windows.bat (v15 launcher)'

Write-Host ''
Write-Host "Synced Archiview v15 to: $V15Root"
Write-Host 'Run run_gui_windows.bat - title should say v15 (not v16).'
