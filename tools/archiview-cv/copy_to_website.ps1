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
        '03_historical_rectified.png',
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

function Get-CuratorFieldsMapFromAnnotations([string]$Path) {
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
            if ($id -le 0) { continue }
            $traceId = [string]$ann.traceId
            $labelRu = [string]$ann.label_ru
            $comment = [string]$ann.comment
            if (-not $traceId -and -not $labelRu -and -not $comment) { continue }
            $map[$id] = @{
                traceId = $traceId
                label_ru = $labelRu
                comment = $comment
            }
        }
    } catch {
        Write-Host "WARN: could not read curator fields from $Path : $_"
    }
    return $map
}

function Get-TraceIdMapFromAnnotations([string]$Path) {
    $map = @{}
    foreach ($entry in (Get-CuratorFieldsMapFromAnnotations $Path).GetEnumerator()) {
        if ($entry.Value.traceId) {
            $map[$entry.Key] = $entry.Value.traceId
        }
    }
    return $map
}

function Merge-WebsiteCuratorFields([string]$Path, [hashtable]$CuratorByAnnotationId) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if ($CuratorByAnnotationId.Count -eq 0) { return }
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
            if (-not $CuratorByAnnotationId.ContainsKey($id)) { continue }
            $fromSite = $CuratorByAnnotationId[$id]
            $changed = $false

            $traceId = [string]$fromSite.traceId
            if ($traceId -and [string]$ann.traceId -ne $traceId) {
                $ann | Add-Member -NotePropertyName traceId -NotePropertyValue $traceId -Force
                $changed = $true
            }

            $labelRu = [string]$fromSite.label_ru
            if ($labelRu -and [string]$ann.label_ru -ne $labelRu) {
                $ann | Add-Member -NotePropertyName label_ru -NotePropertyValue $labelRu -Force
                $changed = $true
            }

            $comment = [string]$fromSite.comment
            if ($comment -and [string]$ann.comment -ne $comment) {
                $ann | Add-Member -NotePropertyName comment -NotePropertyValue $comment -Force
                $changed = $true
            }

            if ($changed) { $merged++ } else { $kept++ }
        }
        Write-JsonUtf8NoBom $Path $data
        Write-Host "OK: curator fields kept for annotations.json (merged=$merged, unchanged=$kept)"
    } catch {
        Write-Host "WARN: curator field merge failed for ${Path}: $_"
    }
}

function Merge-WebsiteTraceIds([string]$Path, [hashtable]$TraceIdByAnnotationId) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if ($TraceIdByAnnotationId.Count -eq 0) { return }
    $curatorMap = @{}
    foreach ($entry in $TraceIdByAnnotationId.GetEnumerator()) {
        $curatorMap[$entry.Key] = @{ traceId = [string]$entry.Value; label_ru = ''; comment = '' }
    }
    Merge-WebsiteCuratorFields $Path $curatorMap
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
    ,@('11_modern_source_for_site.png', 'modern-source.png')
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
        [hashtable]$CuratorFieldsMap = @{}
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
            if ($pair[0] -eq '11_modern_source_for_site.png' -and -not $isSideBySide) {
                $venvPy = Join-Path $ScriptDir '.venv\Scripts\python.exe'
                $exportPy = Join-Path $ScriptDir 'archiview_site_export.py'
                if ((Test-Path -LiteralPath $venvPy) -and (Test-Path -LiteralPath $exportPy)) {
                    try {
                        & $venvPy $exportPy $Result 2>$null
                    } catch { }
                }
            }
            if (-not (Test-Path -LiteralPath $src)) {
                if ($pair[0] -notmatch '^(10_|11_)') {
                    Write-Host "MISSING: $($pair[0]) in $Result"
                }
                continue
            }
        }
        Copy-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "OK: $WebDest\$($pair[1])"
        if ($pair[1] -eq 'annotations.json') {
            Sanitize-WebsiteAnnotations $dst
            Merge-WebsiteCuratorFields $dst $CuratorFieldsMap
            if ($CuratorFieldsMap.Count -gt 0) {
                Merge-WebsiteCuratorFields $src $CuratorFieldsMap
            }
        }
    }
    if ($isSideBySide) {
        $sbMarked = Join-Path $Result '10_side_by_side_marked.png'
        if (Test-Path -LiteralPath $sbMarked) {
            Copy-Item -LiteralPath $sbMarked -Destination (Join-Path $WebDest 'marked-facade.png') -Force
            Write-Host "OK: $WebDest\marked-facade.png (from 10_side_by_side_marked)"
        }
    } else {
        $marked06 = Join-Path $Result '06_marked_rectified.png'
        if (Test-Path -LiteralPath $marked06) {
            Copy-Item -LiteralPath $marked06 -Destination (Join-Path $WebDest 'marked-facade.png') -Force
            Write-Host "OK: $WebDest\marked-facade.png (from 06_marked_rectified)"
        } else {
            Write-Host "WARN: 06_marked_rectified.png missing in $Result"
            Write-Host '      Save markup in Archiview (tab 4) before export. Site uses modern-rectified.png + hover highlights.'
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

function Get-PhotoYearsFromCmpDir {
    param(
        [string]$CmpDir,
        [string]$Title = ''
    )
    $histYear = ''
    $modYear = ''
    $pj = Join-Path $CmpDir 'project_v8.json'
    if (Test-Path -LiteralPath $pj) {
        try {
            $p = Get-Content -LiteralPath $pj -Raw -Encoding UTF8 | ConvertFrom-Json
            $pv = $p.pastvu
            if ($pv) {
                foreach ($key in @('year', 'years', 'date')) {
                    $val = $pv.$key
                    if ($null -ne $val -and [string]$val -match '(\d{4})') {
                        $histYear = $Matches[1]
                        break
                    }
                }
            }
            $ms = $p.modern_source
            if ($ms) {
                foreach ($key in @('captured_at', 'date', 'year')) {
                    $val = $ms.$key
                    if ($null -ne $val -and [string]$val -match '(\d{4})') {
                        $modYear = $Matches[1]
                        break
                    }
                }
            }
        } catch { }
    }
    if (-not $histYear -and $Title -match '\b(1[89]\d{2}|20\d{2})\b') {
        $histYear = $Matches[1]
    }
    return [PSCustomObject]@{ Historical = $histYear; Modern = $modYear }
}

function New-ManifestEntry {
    param(
        [string]$ComparisonId,
        [string]$Title,
        [bool]$IsLegacy,
        [object]$Bundle,
        [string]$RelPrefix,
        [string]$HistoricalPhotoYear = '',
        [string]$ModernPhotoYear = ''
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
        modernSourceUrl = "${prefix}modern-source.png"
        annotationsUrl = "${prefix}annotations.json"
        facadeProjectUrl = "${prefix}facade-project.json"
    }
    if ($HistoricalPhotoYear) { $entry.historicalPhotoYear = $HistoricalPhotoYear }
    if ($ModernPhotoYear) { $entry.modernPhotoYear = $ModernPhotoYear }
    if ($Bundle.IsSideBySide) {
        $entry.sideBySideMarkedUrl = "${prefix}side-by-side-marked.png"
    }
    return $entry
}

function Get-DefaultCuratorFieldsMap([string]$Web, [string]$DefaultCmpId) {
    if ($DefaultCmpId) {
        $cmpAnn = Join-Path $Web ("comparisons\{0}\annotations.json" -f $DefaultCmpId)
        $cmpMap = Get-CuratorFieldsMapFromAnnotations $cmpAnn
        if ($cmpMap.Count -gt 0) { return $cmpMap }
    }
    return Get-CuratorFieldsMapFromAnnotations (Join-Path $Web 'annotations.json')
}

$activeCmpId = Get-ComparisonIdFromResultDir $Result
$defaultCmpId = if ($activeCmpId) { $activeCmpId } else { '' }

$curatorMap = Get-DefaultCuratorFieldsMap -Web $Web -DefaultCmpId $defaultCmpId
if ($curatorMap.Count -gt 0) {
    Write-Host "INFO: will preserve curator fields (traceId, label_ru, comment) for $($curatorMap.Count) annotation id(s) from website"
}

$rootBundle = Export-ComparisonBundle -Result $Result -WebDest $Web -CuratorFieldsMap $curatorMap
$manifestItems = @()
$cmpTitleById = @{}
$cmpStatusById = @{}
$cmpLegacyById = @{}
$cmpHistYearById = @{}
$cmpModYearById = @{}

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
                    $cmpStatusById[$cid] = [string]$cmpMeta.status
                    $cmpLegacyById[$cid] = [bool]$cmpMeta.is_legacy
                    $cmpHistYearById[$cid] = [string]$cmpMeta.historical_year
                    $cmpModYearById[$cid] = [string]$cmpMeta.modern_year
                }
            }
        } catch { }
    }
}

if ($defaultCmpId) {
    $skipRoot = $false
    if ($cmpLegacyById.ContainsKey($defaultCmpId) -and $cmpLegacyById[$defaultCmpId]) {
        $skipRoot = $true
        Write-Host "SKIP: root export is legacy ($defaultCmpId) - not published to website"
    }
    if ($cmpStatusById.ContainsKey($defaultCmpId) -and $cmpStatusById[$defaultCmpId] -eq 'discarded') {
        $skipRoot = $true
        Write-Host "SKIP: root comparison $defaultCmpId is discarded"
    }
    if (-not $skipRoot) {
        $rootTitle = $cmpTitleById[$defaultCmpId]
        if (-not $rootTitle) { $rootTitle = 'Primary (active)' }
        $rootYears = Get-PhotoYearsFromCmpDir -CmpDir $Result -Title $rootTitle
        if ($cmpHistYearById.ContainsKey($defaultCmpId) -and $cmpHistYearById[$defaultCmpId]) {
            $rootYears.Historical = $cmpHistYearById[$defaultCmpId]
        }
        if ($cmpModYearById.ContainsKey($defaultCmpId) -and $cmpModYearById[$defaultCmpId]) {
            $rootYears.Modern = $cmpModYearById[$defaultCmpId]
        }
        if ($rootYears.Historical -and $rootYears.Modern) {
            $rootTitle = "$($rootYears.Historical) -> $($rootYears.Modern)"
        } elseif ($rootYears.Historical) {
            $rootTitle = "$($rootYears.Historical) -> today"
        }
        $manifestItems += New-ManifestEntry -ComparisonId $defaultCmpId -Title $rootTitle -IsLegacy ($defaultCmpId -eq 'cmp_legacy_001') -Bundle $rootBundle -RelPrefix '' -HistoricalPhotoYear $rootYears.Historical -ModernPhotoYear $rootYears.Modern
    }
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
                    Write-Host "SKIP: legacy comparison $cmpId (not exported to website)"
                    continue
                }
                $cmpDir = Join-Path $projDir ("comparisons\{0}" -f $cmpId)
                if (-not (Test-HasExportFiles $cmpDir)) { continue }
                if ($cmpId -eq $defaultCmpId) { continue }
                $destSub = Join-Path $Web ("comparisons\{0}" -f $cmpId)
                $subCuratorMap = Get-CuratorFieldsMapFromAnnotations (Join-Path $destSub 'annotations.json')
                $bundle = Export-ComparisonBundle -Result $cmpDir -WebDest $destSub -CuratorFieldsMap $subCuratorMap
                $title = [string]$cmpMeta.title
                if (-not $title) { $title = $cmpId }
                $years = Get-PhotoYearsFromCmpDir -CmpDir $cmpDir -Title $title
                if ($cmpMeta.historical_year) { $years.Historical = [string]$cmpMeta.historical_year }
                if ($cmpMeta.modern_year) { $years.Modern = [string]$cmpMeta.modern_year }
                if ($years.Historical -and $years.Modern) {
                    $title = "$($years.Historical) -> $($years.Modern)"
                } elseif ($years.Historical) {
                    $title = "$($years.Historical) -> today"
                }
                $manifestItems += New-ManifestEntry -ComparisonId $cmpId -Title $title -IsLegacy $isLegacy -Bundle $bundle -RelPrefix ("comparisons/{0}" -f $cmpId) -HistoricalPhotoYear $years.Historical -ModernPhotoYear $years.Modern
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
