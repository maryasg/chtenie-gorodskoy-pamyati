param(
    [Parameter(Mandatory = $true)]
    [string]$CardId,
    [string]$ProjectDir = '',
    [string]$ComparisonId = '',
    [string]$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati'
)

$ErrorActionPreference = 'Stop'

function Normalize-CardId([string]$Value) {
    if ($Value -match 'MOSCOW_(\d{3})') { return "MOSCOW_$($Matches[1])" }
    return $Value.Trim().ToUpper()
}

$CardId = Normalize-CardId $CardId
$websiteAnn = Join-Path $RepoRoot ("public\explorer\{0}\annotations.json" -f $CardId)
if (-not (Test-Path -LiteralPath $websiteAnn)) {
    throw "Not found on website repo: $websiteAnn"
}

if (-not $ProjectDir) {
    $patterns = @('archiview_cv_easy_v16_package', 'archiview_cv_easy_v15_package')
    $pkg = $null
    foreach ($pattern in $patterns) {
        $hits = Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter $pattern -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($hits) { $pkg = $hits.FullName; break }
    }
    if (-not $pkg) { throw 'Archiview package folder not found on Desktop' }
    $projects = Join-Path $pkg 'archiview_projects'
    if (-not (Test-Path -LiteralPath $projects)) { throw "No archiview_projects in $pkg" }
    Write-Host 'Projects:'
    Get-ChildItem -LiteralPath $projects -Directory | ForEach-Object { Write-Host "  $($_.Name)" }
    $name = Read-Host 'Project folder name (dom so zveryami etc.)'
    $ProjectDir = Join-Path $projects $name
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project not found: $ProjectDir"
}

$targetDir = ''
if ($ComparisonId) {
    $targetDir = Join-Path $ProjectDir ("comparisons\{0}" -f $ComparisonId)
} else {
    $indexPath = Join-Path $ProjectDir 'comparisons\index.json'
    if (Test-Path -LiteralPath $indexPath) {
        $idx = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $active = [string]$idx.active_comparison_id
        if ($active) {
            $targetDir = Join-Path $ProjectDir ("comparisons\{0}" -f $active)
        }
    }
    if (-not $targetDir -or -not (Test-Path -LiteralPath $targetDir)) {
        $legacy = Join-Path $ProjectDir 'result'
        if (Test-Path -LiteralPath $legacy) { $targetDir = $legacy }
    }
}

if (-not $targetDir -or -not (Test-Path -LiteralPath $targetDir)) {
    throw 'Could not find active comparison folder. Pass -ComparisonId cmp_005'
}

$annDir = Join-Path $targetDir 'annotations'
New-Item -ItemType Directory -Path $annDir -Force | Out-Null
$dest = Join-Path $annDir 'manual_annotations.json'
if (Test-Path -LiteralPath $dest) {
    Copy-Item -LiteralPath $dest -Destination ($dest + '.bak') -Force
}
Copy-Item -LiteralPath $websiteAnn -Destination $dest -Force
Write-Host "OK: restored markup to $dest"
Write-Host 'Restart Archiview, open this project, star the same comparison, tab 4 Markup.'
