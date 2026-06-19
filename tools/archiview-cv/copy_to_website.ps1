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
    $CardId = Read-Host 'CardId (required - no default)'
}
$CardId = Normalize-CardId $CardId
if (-not $CardId) {
    Write-Host 'ERROR: CardId is required (MOSCOW_001, MOSCOW_003, ...).'
    if (-not $NoPrompt) { Read-Host 'Press Enter to close' }
    exit 1
}

$Web = Join-Path $RepoRoot ("public\explorer\{0}" -f $CardId)

function Write-JsonUtf8NoBom([string]$Path, [object]$Data) {
    $json = $Data | ConvertTo-Json -Depth 50
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $json, $utf8NoBom)
}

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
            Write-JsonUtf8NoBom $Path $data
            Write-Host 'OK: annotations.json image path sanitized'
        }
    } catch {
        Write-Host "WARN: annotations sanitize failed: $_"
    }
}

function Get-TraceIdMapFromAnnotations([string]$Path) {
    $map = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $map }
    try {
        $data = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($ann in @($data.annotations)) {
            if ($null -eq $ann.id) { continue }
            try {
                $id = [int]$ann.id
            } catch {
                continue
            }
            $traceId = [string]$ann.traceId
            if ($id -gt 0 -and $traceId) {
                $map[$id] = $traceId
            }
        }
    } catch {
        Write-Host "WARN: could not read traceId map from $Path : $_"
    }
    return $map
}

function Merge-WebsiteTraceIds([string]$Path, [hashtable]$TraceIdByAnnotationId) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if ($TraceIdByAnnotationId.Count -eq 0) { return }
    try {
        $data = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        $merged = 0
        $kept = 0
        foreach ($ann in @($data.annotations)) {
            if ($null -eq $ann.id) { continue }
            try {
                $id = [int]$ann.id
            } catch {
                continue
            }
            if (-not $TraceIdByAnnotationId.ContainsKey($id)) { continue }
            $fromSite = [string]$TraceIdByAnnotationId[$id]
            if (-not $fromSite) { continue }
            $existing = [string]$ann.traceId
            if ($existing -eq $fromSite) {
                $kept++
                continue
            }
            $ann | Add-Member -NotePropertyName traceId -NotePropertyValue $fromSite -Force
            $merged++
        }
        Write-JsonUtf8NoBom $Path $data
        Write-Host "OK: traceId links kept for annotations.json (merged=$merged, unchanged=$kept)"
    } catch {
        Write-Host "WARN: traceId merge failed for ${Path}: $_"
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

function Get-ComparisonIdFromResultDir([string]$Dir) {
    $leaf = Split-Path -Leaf $Dir
    if ($leaf -eq 'result') { return 'cmp_legacy_001' }
    if ((Split-Path -Parent $Dir | Split-Path -Leaf) -eq 'comparisons') { return $leaf }
    return ''
}

function Get-AnnotationCount([string]$AnnPath) {
    if (-not (Test-Path -LiteralPath $AnnPath)) { return 0 }
    try {
        $data = Get-Content -LiteralPath $AnnPath -Raw -Encoding UTF8 | ConvertFrom-Json
        return @($data.annotations).Count
    } catch {
        return 0
    }
}

function Export-ComparisonBundle {
    param(
        [Parameter(Mandatory = $true)][string]$Result,
        [Parameter(Mandatory = $true)][string]$WebDest,
        [hashtable]$TraceIdMap = @{}
    )
    if (-not (Test-Path -LiteralPath $WebDest)) {
        New-Item -ItemType Directory -Path $WebDest -Force | Out-Null
    }
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
        $dst = Join-Path $WebDest $pair[1]
        if (-not (Test-Path -LiteralPath $src)) {
            if ($pair[0] -notmatch '^10_') {
                Write-Host "MISSING: $($pair[0]) in $Result"
            }
            continue
        }
        Copy-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "OK: $WebDest\$($pair[1])"
        if ($pair[1] -eq 'annotations.json') {
            Sanitize-WebsiteAnnotations $dst
            Merge-WebsiteTraceIds $dst $TraceIdMap
            if ($TraceIdMap.Count -gt 0) {
                Merge-WebsiteTraceIds $src $TraceIdMap
            }
        }
    }
    if (-not $isSideBySide) {
        $marked06 = Join-Path $Result '06_marked_rectified.png'
        if (Test-Path -LiteralPath $marked06) {
            Copy-Item -LiteralPath $marked06 -Destination (Join-Path $WebDest 'marked-facade.png') -Force
            Write-Host "OK: $WebDest\marked-facade.png (from 06_labeling_canvas)"
        }
    }
    $ProjectJson = Join-Path $Result 'project_v8.json'
    $OutJson = Join-Path $WebDest 'facade-project.json'
    if (Test-Path -LiteralPath $ProjectJson) {
        & (Join-Path $ScriptDir 'export_facade_project.ps1') -ProjectJson $ProjectJson -OutJson $OutJson
        Write-Host "OK: $WebDest\facade-project.json"
    }
    return [PSCustomObject]@{
        IsSideBySide = $isSideBySide
        AnnotationCount = (Get-AnnotationCount (Join-Path $WebDest 'annotations.json'))
    }
}

function New-ManifestEntry {
    param(
        [string]$ComparisonId,
        [string]$Title,
        [bool]$IsLegacy,
        [object]$Bundle,
        [string]$RelPrefix
    )
    $layout = if ($Bundle.IsSideBySide) { 'side_by_side' } else { 'overlay' }
    $prefix = if ($RelPrefix -and $RelPrefix -ne '.') { "$RelPrefix/" } else { '' }
    $entry = [ordered]@{
        comparisonId = $ComparisonId
        title = $Title
        labelingLayout = $layout
        annotationCount = [int]$Bundle.AnnotationCount
        isLegacy = [bool]$IsLegacy
        markedFacadeUrl = if ($Bundle.IsSideBySide) {
            "${prefix}side-by-side-marked.png"
        } else {
            "${prefix}marked-facade.png"
        }
        labeledFacadeUrl = "${prefix}marked-facade-labeled.png"
        historicalRectifiedUrl = "${prefix}historical-rectified.png"
        modernRectifiedUrl = "${prefix}modern-rectified.png"
        annotationsUrl = "${prefix}annotations.json"
        facadeProjectUrl = "${prefix}facade-project.json"
    }
    if ($Bundle.IsSideBySide) {
        $entry.sideBySideMarkedUrl = "${prefix}side-by-side-marked.png"
    }
    return $entry
}

$activeCmpId = Get-ComparisonIdFromResultDir $Result
$defaultCmpId = if ($activeCmpId) { $activeCmpId } else { '' }

$existingAnnPath = Join-Path $Web 'annotations.json'
$traceIdMap = Get-TraceIdMapFromAnnotations $existingAnnPath
if ($traceIdMap.Count -gt 0) {
    Write-Host "INFO: will preserve traceId for $($traceIdMap.Count) annotation id(s) from website"
}

$rootBundle = Export-ComparisonBundle -Result $Result -WebDest $Web -TraceIdMap $traceIdMap
$manifestItems = @()
$cmpTitleById = @{}

$projDir = Get-ProjectDirFromResult $Result
if ($projDir) {
    $indexPath = Join-Path $projDir 'comparisons\index.json'
    if (Test-Path -LiteralPath $indexPath) {
        try {
            $idx = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if (-not $defaultCmpId -and $idx.active_comparison_id) {
                $defaultCmpId = [string]$idx.active_comparison_id
            }
            foreach ($cmpMeta in @($idx.comparisons)) {
                $cid = [string]$cmpMeta.comparison_id
                if ($cid) {
                    $cmpTitleById[$cid] = [string]$cmpMeta.title
                }
            }
        } catch { }
    }
}

if ($defaultCmpId) {
    $rootTitle = $cmpTitleById[$defaultCmpId]
    if (-not $rootTitle) { $rootTitle = 'Primary (active)' }
    $manifestItems += New-ManifestEntry -ComparisonId $defaultCmpId -Title $rootTitle -IsLegacy ($defaultCmpId -eq 'cmp_legacy_001') -Bundle $rootBundle -RelPrefix ''
}

if ($projDir) {
    $indexPath = Join-Path $projDir 'comparisons\index.json'
    if (Test-Path -LiteralPath $indexPath) {
        try {
            $idx = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
            foreach ($cmpMeta in @($idx.comparisons)) {
                $cmpId = [string]$cmpMeta.comparison_id
                if (-not $cmpId) { continue }
                $status = [string]$cmpMeta.status
                if ($status -eq 'discarded') { continue }
                $isLegacy = [bool]$cmpMeta.is_legacy
                if ($isLegacy) {
                    $cmpDir = Join-Path $projDir 'result'
                } else {
                    $cmpDir = Join-Path $projDir ("comparisons\{0}" -f $cmpId)
                }
                if (-not (Test-HasExportFiles $cmpDir)) { continue }
                if ($cmpId -eq $defaultCmpId) { continue }
                $destSub = Join-Path $Web ("comparisons\{0}" -f $cmpId)
                $subTraceMap = Get-TraceIdMapFromAnnotations (Join-Path $destSub 'annotations.json')
                $bundle = Export-ComparisonBundle -Result $cmpDir -WebDest $destSub -TraceIdMap $subTraceMap
                if ([int]$bundle.AnnotationCount -le 0) { continue }
                $title = [string]$cmpMeta.title
                if (-not $title) { $title = $cmpId }
                $manifestItems += New-ManifestEntry -ComparisonId $cmpId -Title $title -IsLegacy $isLegacy -Bundle $bundle -RelPrefix ("comparisons/{0}" -f $cmpId)
                Write-Host "OK: exported comparison $cmpId ($title)"
            }
        } catch {
            Write-Host "WARN: could not export extra comparisons: $_"
        }
    }
}

if ($manifestItems.Count -gt 0) {
    $manifest = [ordered]@{
        cardId = $CardId
        defaultComparisonId = $defaultCmpId
        comparisons = $manifestItems
        updatedAt = (Get-Date).ToUniversalTime().ToString('o')
    }
    Write-JsonUtf8NoBom (Join-Path $Web 'manifest.json') $manifest
    Write-Host "OK: manifest.json ($($manifestItems.Count) comparison(s))"
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
