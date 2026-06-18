param(
    [string]$V16Root = ''
)

$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot

if (-not $V16Root) {
    $patterns = @('archiview_cv_easy_v16_package', 'archiview_cv_easy_v15_package')
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
        throw 'Archiview package folder not found under Desktop\Cult Tech (expected archiview_cv_easy_v16_package or v15_package)'
    }
    $V16Root = $found.FullName
}

$files = @(
    'run_gui_windows.bat',
    'copy_to_website.bat',
    'copy_to_website.ps1',
    'sync_to_v16_desktop.ps1',
    'sync_to_v15_desktop.ps1',
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
    Copy-Item -LiteralPath $from -Destination (Join-Path $V16Root $name) -Force
    Write-Host "OK: $name"
}

Write-Host ''
Write-Host "Synced Archiview v16 files to: $V16Root"
Write-Host 'Next: run run_gui_windows.bat from that folder.'
