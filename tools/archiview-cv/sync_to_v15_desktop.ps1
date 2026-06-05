param(
    [string]$V15Root = ''
)

$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot

if (-not $V15Root) {
    $hits = Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter 'archiview_cv_easy_v15_package' -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $hits) {
        throw 'v15 package folder not found under Desktop\Cult Tech'
    }
    $V15Root = $hits.FullName
}

$files = @(
    'run_gui_windows.bat',
    'copy_to_website.bat',
    'copy_to_website.ps1',
    'update_website_registry.ps1',
    'export_facade_project.ps1',
    'website_buildings.json',
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

Write-Host ''
Write-Host "Synced to: $V15Root"
