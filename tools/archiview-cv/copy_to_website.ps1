param(
    [string]$CardId = '',
    [string]$ResultDir = '',
    [string]$ProjectFolder = '20260520_190036',
    [string]$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati',
    [switch]$NoPrompt
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $CardId -and -not $NoPrompt) {
    Write-Host ''
    Write-Host 'Building ID for the website (see website_buildings.json):'
    Write-Host '  MOSCOW_003 - Dom so zveryami'
    Write-Host '  MOSCOW_001 - Ordynka 17'
    Write-Host '  MOSCOW_002, MOSCOW_004 - when added to json'
    $CardId = Read-Host 'CardId (Enter = MOSCOW_003)'
}
if (-not $CardId) { $CardId = 'MOSCOW_003' }

$Web = Join-Path $RepoRoot ("public\explorer\{0}" -f $CardId)

function Test-HasExportFiles([string]$Dir) {
    if (-not (Test-Path -LiteralPath $Dir)) { return $false }
    $markers = @(
        '04_modern_rectified.png',
        '07_marked_on_original_modern.png',
        'annotations\manual_annotations.json'
    )
    foreach ($name in $markers) {
        if (Test-Path -LiteralPath (Join-Path $Dir $name)) { return $true }
    }
    return $false
}

function Find-ResultFolder {
    param([string]$StartDir, [string]$ProjectFolder, [string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) { return $Explicit }

    $direct = Join-Path $StartDir "archiview_projects\$ProjectFolder\result"
    if (Test-HasExportFiles $direct) { return $direct }

    $projectsRoot = Join-Path $StartDir 'archiview_projects'
    if (Test-Path -LiteralPath $projectsRoot) {
        $candidates = New-Object System.Collections.Generic.List[string]
        Get-ChildItem -LiteralPath $projectsRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $proj = $_.FullName
            $indexPath = Join-Path $proj 'comparisons\index.json'
            if (Test-Path -LiteralPath $indexPath) {
                try {
                    $idx = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
                    $activeId = [string]$idx.active_comparison_id
                    if ($activeId) {
                        $cmpDir = Join-Path $proj ("comparisons\{0}" -f $activeId)
                        if (Test-Path -LiteralPath $cmpDir) { [void]$candidates.Add($cmpDir) }
                    }
                } catch {
                    # ignore broken index.json
                }
            }
            $legacy = Join-Path $proj 'result'
            if (Test-Path -LiteralPath $legacy) { [void]$candidates.Add($legacy) }
            Get-ChildItem -LiteralPath (Join-Path $proj 'comparisons') -Directory -ErrorAction SilentlyContinue |
                ForEach-Object { [void]$candidates.Add($_.FullName) }
        }
        $sorted = $candidates | Sort-Object { (Get-Item -LiteralPath $_).LastWriteTime } -Descending -Unique
        foreach ($dir in $sorted) {
            if (Test-HasExportFiles $dir) { return $dir }
        }
    }

    $cultTech = Join-Path $env:USERPROFILE 'Desktop\Cult Tech'
    if (Test-Path -LiteralPath $cultTech) {
        $matches = Get-ChildItem -LiteralPath $cultTech -Recurse -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq 'result' -and $_.Parent.Name -eq $ProjectFolder } |
            Select-Object -First 1
        if ($matches -and (Test-HasExportFiles $matches.FullName)) { return $matches.FullName }
    }

    if (Test-Path -LiteralPath (Join-Path $StartDir 'archiview_projects')) {
        $latest = Get-ChildItem -LiteralPath (Join-Path $StartDir 'archiview_projects') -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($latest) {
            $candidate = Join-Path $latest.FullName 'result'
            if (Test-HasExportFiles $candidate) { return $candidate }
        }
    }
    return $null
}

$Result = Find-ResultFolder -StartDir $ScriptDir -ProjectFolder $ProjectFolder -Explicit $ResultDir

Write-Host ''
Write-Host 'FROM (Archiview result):'
if ($Result) { Write-Host "  $Result" } else { Write-Host '  NOT FOUND' }
Write-Host 'TO (website folder):'
Write-Host "  $Web"
Write-Host "CardId: $CardId"
Write-Host ''

if (-not $Result) {
    Write-Host 'ERROR: result folder not found.'
    Write-Host 'Tip: in Archiview use active comparison (star) or pass -ResultDir path to cmp folder.'
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
    ,@('10_side_by_side_marked.png', 'side-by-side-marked.png')
)

foreach ($pair in $Pairs) {
    $src = Join-Path $Result $pair[0]
    $dst = Join-Path $Web $pair[1]
    if (-not (Test-Path -LiteralPath $src)) {
        if ($pair[0] -notmatch '^10_') {
            Write-Host "MISSING: $($pair[0])"
        }
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
