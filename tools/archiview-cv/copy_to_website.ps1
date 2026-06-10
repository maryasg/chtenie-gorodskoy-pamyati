param(
    [string]$CardId = '',
    [string]$ResultDir = '',
    [string]$ProjectFolder = '20260520_190036',
    [string]$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati',
    [switch]$NoPrompt
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Normalize-CardId([string]$Value) {
    if (-not $Value) { return '' }
    if ($Value -match 'MOSCOW_(\d{3})') { return "MOSCOW_$($Matches[1])" }
    return $Value.Trim().ToUpper()
}

if (-not $CardId -and -not $NoPrompt) {
    Write-Host ''
    Write-Host 'Building ID for the website (see website_buildings.json):'
    Write-Host '  MOSCOW_001 - Dom Kumaninykh / Ordynka 17'
    Write-Host '  MOSCOW_003 - Dom so zveryami'
    Write-Host '  MOSCOW_004 - Dom s vyveskoy Falkevicha (Krivokolennyy)'
    Write-Host '  MOSCOW_002 - when added to json'
    $CardId = Read-Host 'CardId (required — no default)'
}
$CardId = Normalize-CardId $CardId
if (-not $CardId) {
    Write-Host 'ERROR: CardId is required (MOSCOW_001, MOSCOW_003, …).'
    if (-not $NoPrompt) { Read-Host 'Press Enter to close' }
    exit 1
}

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

function Sanitize-WebsiteAnnotations([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        $data = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        $imageRef = [string]$data.image
        if (-not $imageRef) { return }

        $leaf = Split-Path -Leaf $imageRef
        if (-not $leaf) {
            $leaf = $imageRef -replace '^.*[\\/]', ''
        }
        if ($leaf -and $leaf -ne $imageRef) {
            $data.image = $leaf
            $data | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $Path -Encoding UTF8
            Write-Host 'OK: annotations.json image path sanitized'
        }
    } catch {
        Write-Host "WARN: annotations sanitize failed: $_"
    }
}

function Get-ProjectDirFromResult([string]$Dir) {
    $p = Get-Item -LiteralPath $Dir
    if ($p.Name -eq 'result') { return $p.Parent.FullName }
    if ($p.Parent.Name -eq 'comparisons') { return $p.Parent.Parent.FullName }
    return $null
}

function Get-SiteCardFromResult([string]$Dir) {
    $proj = Get-ProjectDirFromResult $Dir
    if (-not $proj) { return '' }
    $house = Join-Path $proj 'house.json'
    if (-not (Test-Path -LiteralPath $house)) { return '' }
    try {
        $h = Get-Content -LiteralPath $house -Raw -Encoding UTF8 | ConvertFrom-Json
        return (Normalize-CardId ([string]$h.site_card_id))
    } catch {
        return ''
    }
}

function Test-ExportMatchesCardId([string]$Dir, [string]$ExpectedCardId) {
    $expected = Normalize-CardId $ExpectedCardId
    $actual = Get-SiteCardFromResult $Dir
    if ($actual) {
        if ($actual -eq $expected) { return $true }
        Write-Host "BLOCKED: export is from project $actual, but CardId=$expected"
        return $false
    }
    $ann = Join-Path $Dir 'annotations\manual_annotations.json'
    if (Test-Path -LiteralPath $ann) {
        try {
            $data = Get-Content -LiteralPath $ann -Raw -Encoding UTF8 | ConvertFrom-Json
            $imageRef = ([string]$data.image).ToLower()
            $keywords = @{
                'MOSCOW_001' = @('kumanin', 'ordynk', 'ardov', 'ordynka', 'bolshaya_ordynka')
                'MOSCOW_003' = @('zver', 'chistoprud', 'so_zver', 'dom_so_zver')
                'MOSCOW_004' = @('krivokol', 'falkev', 'falkevich', 'krivokolenny')
            }
            foreach ($kw in $keywords[$expected]) {
                if ($imageRef -like "*$kw*") { return $true }
            }
        } catch {
            # fall through
        }
    }
    Write-Host "BLOCKED: cannot verify export belongs to $expected (set site_card_id in house.json)."
    return $false
}

function Find-ResultFolder {
    param([string]$StartDir, [string]$ProjectFolder, [string]$Explicit, [string]$CardId)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) {
        if (Test-ExportMatchesCardId $Explicit $CardId) { return $Explicit }
        return $null
    }

    $projectsRoot = Join-Path $StartDir 'archiview_projects'
    if (-not (Test-Path -LiteralPath $projectsRoot)) { return $null }

    $candidates = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $projectsRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $proj = $_.FullName
        $projCard = ''
        $house = Join-Path $proj 'house.json'
        if (Test-Path -LiteralPath $house) {
            try {
                $h = Get-Content -LiteralPath $house -Raw -Encoding UTF8 | ConvertFrom-Json
                $projCard = Normalize-CardId ([string]$h.site_card_id)
            } catch { }
        }
        if ($projCard -and $projCard -ne (Normalize-CardId $CardId)) { return }

        $indexPath = Join-Path $proj 'comparisons\index.json'
        if (Test-Path -LiteralPath $indexPath) {
            try {
                $idx = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $activeId = [string]$idx.active_comparison_id
                if ($activeId) {
                    $cmpDir = Join-Path $proj ("comparisons\{0}" -f $activeId)
                    if (Test-Path -LiteralPath $cmpDir) { [void]$candidates.Add($cmpDir) }
                }
            } catch { }
        }
        $legacy = Join-Path $proj 'result'
        if (Test-Path -LiteralPath $legacy) { [void]$candidates.Add($legacy) }
    }

    $sorted = $candidates | Sort-Object { (Get-Item -LiteralPath $_).LastWriteTime } -Descending -Unique
    foreach ($dir in $sorted) {
        if (-not (Test-HasExportFiles $dir)) { continue }
        if (Test-ExportMatchesCardId $dir $CardId) { return $dir }
    }
    return $null
}

$Result = Find-ResultFolder -StartDir $ScriptDir -ProjectFolder $ProjectFolder -Explicit $ResultDir -CardId $CardId

Write-Host ''
Write-Host 'FROM (Archiview result):'
if ($Result) { Write-Host "  $Result" } else { Write-Host '  NOT FOUND' }
Write-Host 'TO (website folder):'
Write-Host "  $Web"
Write-Host "CardId: $CardId"
Write-Host ''

if (-not $Result) {
    Write-Host 'ERROR: result folder not found or CardId mismatch.'
    Write-Host 'Tip: open the correct house in Archiview, star the comparison, use "Na sait" from the app.'
    Write-Host 'Or: copy_to_website.bat with matching CardId and active project.'
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

$isSideBySide = $false
$annExport = Join-Path $Result 'annotations\manual_annotations.json'
if (Test-Path -LiteralPath $annExport) {
    try {
        $annData = Get-Content -LiteralPath $annExport -Raw -Encoding UTF8 | ConvertFrom-Json
        if ([string]$annData.labeling_layout -eq 'side_by_side') { $isSideBySide = $true }
    } catch { }
}

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
    if ($pair[1] -eq 'annotations.json') {
        Sanitize-WebsiteAnnotations $dst
    }
}

if (-not $isSideBySide) {
    $marked06 = Join-Path $Result '06_marked_rectified.png'
    if (Test-Path -LiteralPath $marked06) {
        Copy-Item -LiteralPath $marked06 -Destination (Join-Path $Web 'marked-facade.png') -Force
        Write-Host 'OK: marked-facade.png (from 06_labeling_canvas, same as markup tab)'
    }
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
