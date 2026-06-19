param(
    [string]$V16Root = ''
)

$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot

function Resolve-PathNormalized([string]$Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return $null }
    return (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\')
}

function Find-GitArchiviewTools {
    $candidates = @(
        (Join-Path $env:USERPROFILE 'Projects\chtenie-gorodskoy-pamyati\tools\archiview-cv')
    )
    foreach ($candidate in $candidates) {
        $gui = Join-Path $candidate 'archiview_gui.py'
        if (Test-Path -LiteralPath $gui) { return $candidate }
    }
    return $null
}

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

$V16Resolved = Resolve-PathNormalized $V16Root
$SrcResolved = Resolve-PathNormalized $Src
if ($SrcResolved -and $V16Resolved -and $SrcResolved -eq $V16Resolved) {
    $gitSrc = Find-GitArchiviewTools
    if ($gitSrc) {
        Write-Host 'NOTE: using git tools as sync source (not Desktop v16 folder):'
        Write-Host "  $gitSrc"
        $Src = $gitSrc
    } else {
        throw @'
SYNC ERROR: setup was run from the Desktop v16 package folder.

Run from git repo in cmd:
  cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati
  git pull
  cd tools\archiview-cv
  setup_v16_desktop.bat

Or double-click OBNOVIT_IZ_GITA.bat in the v16 Desktop folder.
'@
    }
}

$files = @(
    'install_windows.bat',
    'PERESOZDAT_VENV.bat',
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
    'setup_v16_desktop.ps1',
    'setup_v16_desktop.bat',
    'OBNOVIT_IZ_GITA.bat',
    'PROVERIT_OBNOVLENIE.bat',
    'update_website_registry.ps1',
    'export_facade_project.ps1',
    'export_moscow001_from_v15.ps1',
    'restore_markup_from_website.ps1',
    'restore_markup_from_website.bat',
    'website_buildings.json',
    'README_v16_ru.md',
    'ENCODING_RULES.md',
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

function Get-BuildVersionLabel {
    param([string]$RepoRoot)
    if (-not $RepoRoot -or -not (Test-Path -LiteralPath $RepoRoot)) {
        return 'v16 polygon edit'
    }
    try {
        Push-Location -LiteralPath $RepoRoot
        $hash = (git rev-parse --short HEAD 2>$null)
        if ($hash) {
            $date = Get-Date -Format 'yyyy-MM-dd'
            return "v16 $date $hash"
        }
    } catch {
    } finally {
        Pop-Location
    }
    return 'v16 polygon edit'
}

$repoForVersion = $Src
$gitTools = Find-GitArchiviewTools
if ($gitTools) {
    $maybeRepo = (Resolve-Path -LiteralPath (Join-Path $gitTools '..\..')).Path
    if (Test-Path -LiteralPath (Join-Path $maybeRepo '.git')) {
        $repoForVersion = $maybeRepo
    }
}
$versionLabel = Get-BuildVersionLabel $repoForVersion

$launcherV16 = Join-Path $Src 'run_gui_v16.bat'
$launcherDest = Join-Path $V16Root 'run_gui_windows.bat'
Copy-Item -LiteralPath $launcherV16 -Destination $launcherDest -Force
Write-Host 'OK: run_gui_windows.bat (v16 launcher)'
Copy-Item -LiteralPath $launcherV16 -Destination (Join-Path $V16Root 'ZAPUSK_V16.bat') -Force
Write-Host 'OK: ZAPUSK_V16.bat'
Set-Content -LiteralPath (Join-Path $V16Root 'ARCHIVIEW_VERSION.txt') -Value $versionLabel -Encoding UTF8
Write-Host "OK: ARCHIVIEW_VERSION.txt ($versionLabel)"

Write-Host ''
Write-Host '============================================'
Write-Host 'DONE. v16 folder:'
Write-Host $V16Root
Write-Host 'Run: ZAPUSK_V16.bat'
Write-Host 'Window title must say: v16 polygon edit'
Write-Host '============================================'
