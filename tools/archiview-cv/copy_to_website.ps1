param(
    [string]$CardId = '',
    [string]$ResultDir = '',
    [string]$ProjectId = '20260520_190036',
    [string]$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati',
    [switch]$NoPrompt
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $CardId -and -not $NoPrompt) {
    Write-Host ''
    Write-Host 'ID здания на сайте (из website_buildings.json):'
    Write-Host '  MOSCOW_003 — Дом со зверями'
    Write-Host '  MOSCOW_001 — Ордынка 17'
    Write-Host '  MOSCOW_002, MOSCOW_004 — когда добавите в json'
    $CardId = Read-Host 'CardId (Enter = MOSCOW_003)'
}
if (-not $CardId) { $CardId = 'MOSCOW_003' }

$Web = Join-Path $RepoRoot ("public\explorer\{0}" -f $CardId)

function Find-ResultFolder {
    param([string]$StartDir, [string]$Pid, [string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) { return $Explicit }

    $direct = Join-Path $StartDir "archiview_projects\$Pid\result"
    if (Test-Path -LiteralPath $direct) { return $direct }

    $cultTech = Join-Path $env:USERPROFILE 'Desktop\Cult Tech'
    if (Test-Path -LiteralPath $cultTech) {
        $matches = Get-ChildItem -LiteralPath $cultTech -Recurse -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq 'result' -and $_.Parent.Name -eq $Pid } |
            Select-Object -First 1
        if ($matches) { return $matches.FullName }
    }

    $latest = Get-ChildItem -LiteralPath (Join-Path $StartDir 'archiview_projects') -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($latest) {
        $candidate = Join-Path $latest.FullName 'result'
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

$Result = Find-ResultFolder -StartDir $ScriptDir -Pid $ProjectId -Explicit $ResultDir

Write-Host ''
Write-Host 'FROM (Archiview result):'
if ($Result) { Write-Host "  $Result" } else { Write-Host '  NOT FOUND' }
Write-Host 'TO (website folder):'
Write-Host "  $Web"
Write-Host "CardId: $CardId"
Write-Host ''

if (-not $Result) {
    Write-Host 'ERROR: result folder not found.'
    Write-Host 'Run from archiview v15 folder or pass -ResultDir path to result/.'
    if (-not $NoPrompt) { Read-Host 'Press Enter to close' }
    exit 1
}

if (-not (Test-Path -LiteralPath $Web)) {
    New-Item -ItemType Directory -Path $Web -Force | Out-Null
}

$Pairs = @(
    ,@('07_marked_on_original_modern.png', 'marked-facade.png')
    ,@('08_marked_on_original_modern_labeled.png', 'marked-facade-labeled.png')
    ,@('annotations\manual_annotations.json', 'annotations.json')
    ,@('03_historical_rectified.png', 'historical-rectified.png')
    ,@('04_modern_rectified.png', 'modern-rectified.png')
)

foreach ($pair in $Pairs) {
    $src = Join-Path $Result $pair[0]
    $dst = Join-Path $Web $pair[1]
    if (-not (Test-Path -LiteralPath $src)) {
        Write-Host "MISSING: $($pair[0])"
        continue
    }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    Write-Host "OK: $($pair[1])"
}

$ProjectJson = Join-Path $Result 'project_v8.json'
$OutJson = Join-Path $Web 'facade-project.json'
if (Test-Path -LiteralPath $ProjectJson) {
    & (Join-Path $ScriptDir 'export_facade_project.ps1') -ProjectJson $ProjectJson -OutJson $OutJson
    Write-Host 'OK: facade-project.json'
} else {
    Write-Host 'MISSING: project_v8.json'
}

Write-Host ''
Write-Host 'Updating website registry (archiviewAssets.ts + verification)...'
try {
    & (Join-Path $ScriptDir 'update_website_registry.ps1') -CardId $CardId -RepoRoot $RepoRoot -ScriptDir $ScriptDir
} catch {
    Write-Host "WARN: registry update failed: $_"
    Write-Host 'Photos copied; add entry manually or fix website_buildings.json'
}

Write-Host ''
Write-Host 'Done. Next: GitHub Desktop -> Commit -> Push origin'
if (-not $NoPrompt) { Read-Host 'Press Enter to close' }
