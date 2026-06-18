param(
    [string]$V15Root = '',
    [string]$V16Root = ''
)

$ErrorActionPreference = 'Stop'

function Find-DesktopPackage([string]$FolderName) {
    $root = Join-Path $env:USERPROFILE 'Desktop\Cult Tech'
    if (-not (Test-Path -LiteralPath $root)) { return $null }
    return Get-ChildItem -LiteralPath $root -Recurse -Directory -Filter $FolderName -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

if (-not $V15Root) {
    $found = Find-DesktopPackage 'archiview_cv_easy_v15_package'
    if (-not $found) {
        throw 'archiview_cv_easy_v15_package not found. Install v15 first.'
    }
    $V15Root = $found.FullName
}

if (-not $V16Root) {
    $parent = Split-Path -Parent $V15Root
    $V16Root = Join-Path $parent 'archiview_cv_easy_v16_package'
}

if (-not (Test-Path -LiteralPath $V15Root)) {
    throw "v15 folder not found: $V15Root"
}

if (Test-Path -LiteralPath $V16Root) {
    Write-Host "v16 folder already exists:"
    Write-Host "  $V16Root"
    Write-Host 'Skip copy - will only update files.'
    exit 0
}

Write-Host "Copy v15 -> v16 (without .venv):"
Write-Host "  from: $V15Root"
Write-Host "  to:   $V16Root"

New-Item -ItemType Directory -Path $V16Root -Force | Out-Null
Get-ChildItem -LiteralPath $V15Root -Force | Where-Object { $_.Name -ne '.venv' } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $V16Root $_.Name) -Recurse -Force
}

Write-Host ''
Write-Host 'Done. Next steps:'
Write-Host '  1. cd tools\archiview-cv in git repo'
Write-Host '  2. powershell -File .\sync_to_v16_desktop.ps1'
Write-Host '  3. Open v16 folder, run install_windows.bat if .venv missing'
Write-Host '  4. run_gui_windows.bat (v16)'
