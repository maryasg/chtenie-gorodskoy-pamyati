param(
    [Parameter(Mandatory = $true)]
    [string]$CardId,
    [string]$ProjectDir = '',
    [string]$ComparisonId = '',
    [string]$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati',
    [switch]$AllComparisons
)

$ErrorActionPreference = 'Stop'

function Normalize-CardId([string]$Value) {
    if ($Value -match 'MOSCOW_(\d{3})') { return "MOSCOW_$($Matches[1])" }
    return $Value.Trim().ToUpper()
}

function Read-JsonFile([string]$Path) {
    $text = [System.IO.File]::ReadAllText($Path)
    if ($text.Length -gt 0 -and [int][char]$text[0] -eq 0xFEFF) {
        $text = $text.Substring(1)
    }
    return $text | ConvertFrom-Json
}

function Write-JsonUtf8NoBom([string]$Path, [object]$Data) {
    $json = $Data | ConvertTo-Json -Depth 50
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $json, $utf8NoBom)
}

function Find-ProjectByCardId([string]$ProjectsRoot, [string]$Card) {
    if (-not (Test-Path -LiteralPath $ProjectsRoot)) { return $null }
    foreach ($dir in Get-ChildItem -LiteralPath $ProjectsRoot -Directory) {
        foreach ($housePath in @(
            (Join-Path $dir.FullName 'house.json'),
            (Join-Path $dir.FullName 'metadata\house.json')
        )) {
            if (-not (Test-Path -LiteralPath $housePath)) { continue }
            try {
                $h = Read-JsonFile $housePath
                $site = [string]$h.site_card_id
                if ($site -and ((Normalize-CardId $site) -eq $Card)) {
                    return $dir.FullName
                }
            } catch { }
        }
    }
    return $null
}

function Get-RestoreTargets([string]$ProjectDir, [string]$ComparisonId, [switch]$AllComparisons) {
    $targets = New-Object 'System.Collections.Generic.List[string]'
    $seen = @{}

    function Add-Target([string]$Dir) {
        if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) { return }
        $key = (Resolve-Path -LiteralPath $Dir).Path
        if ($seen.ContainsKey($key)) { return }
        $seen[$key] = $true
        [void]$targets.Add($key)
    }

    if ($ComparisonId) {
        Add-Target (Join-Path $ProjectDir ("comparisons\{0}" -f $ComparisonId))
        return ,$targets.ToArray()
    }

    $indexPath = Join-Path $ProjectDir 'comparisons\index.json'
    if (Test-Path -LiteralPath $indexPath) {
        try {
            $idx = Read-JsonFile $indexPath
            $active = [string]$idx.active_comparison_id
            if ($active) {
                Add-Target (Join-Path $ProjectDir ("comparisons\{0}" -f $active))
            }
            if ($AllComparisons) {
                foreach ($cmp in @($idx.comparisons)) {
                    $id = [string]$cmp.comparison_id
                    if ($id) {
                        Add-Target (Join-Path $ProjectDir ("comparisons\{0}" -f $id))
                    }
                }
            }
        } catch { }
    }

    Add-Target (Join-Path $ProjectDir 'result')

    if ($targets.Count -eq 0) {
        throw 'Could not find comparison or result folder. Pass -ComparisonId cmp_005'
    }
    return ,$targets.ToArray()
}

$CardId = Normalize-CardId $CardId
$websiteAnn = Join-Path $RepoRoot ("public\explorer\{0}\annotations.json" -f $CardId)
if (-not (Test-Path -LiteralPath $websiteAnn)) {
    throw "Not found on website repo: $websiteAnn"
}

$annData = Read-JsonFile $websiteAnn
$annCount = @($annData.annotations).Count
if ($annCount -eq 0) {
    throw "Website file has 0 regions: $websiteAnn"
}
Write-Host "Website: $annCount region(s) in $websiteAnn"

if (-not $ProjectDir) {
    $patterns = @('archiview_cv_easy_v15_package', 'archiview_cv_easy_v16_package')
    $pkg = $null
    foreach ($pattern in $patterns) {
        $hits = Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter $pattern -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($hits) { $pkg = $hits.FullName; break }
    }
    if (-not $pkg) { throw 'Archiview package folder not found on Desktop' }
    $projects = Join-Path $pkg 'archiview_projects'
    if (-not (Test-Path -LiteralPath $projects)) { throw "No archiview_projects in $pkg" }

    $ProjectDir = Find-ProjectByCardId $projects $CardId
    if ($ProjectDir) {
        Write-Host "Found project by site_card_id: $ProjectDir"
    } else {
        Write-Host 'Projects:'
        Get-ChildItem -LiteralPath $projects -Directory | ForEach-Object { Write-Host "  $($_.Name)" }
        $name = Read-Host 'Project folder name (dom so zveryami etc.)'
        $ProjectDir = Join-Path $projects $name
    }
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project not found: $ProjectDir"
}

$targetDirs = Get-RestoreTargets -ProjectDir $ProjectDir -ComparisonId $ComparisonId -AllComparisons:$AllComparisons
foreach ($targetDir in $targetDirs) {
    $annDir = Join-Path $targetDir 'annotations'
    New-Item -ItemType Directory -Path $annDir -Force | Out-Null
    $dest = Join-Path $annDir 'manual_annotations.json'
    if (Test-Path -LiteralPath $dest) {
        Copy-Item -LiteralPath $dest -Destination ($dest + '.bak') -Force
    }
    Write-JsonUtf8NoBom $dest $annData
    $verify = Read-JsonFile $dest
    $n = @($verify.annotations).Count
    Write-Host "OK: $n region(s) -> $dest"
}

Write-Host ''
Write-Host 'Done. Fully quit Archiview (close window), run again, open this project, tab 4 Markup.'
Write-Host ("Regions in status bar (tab 4): " + $annCount)
