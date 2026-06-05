param(
    [Parameter(Mandatory = $true)][string]$CardId,
    [Parameter(Mandatory = $true)][string]$RepoRoot,
    [string]$ScriptDir = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

$configPath = Join-Path $ScriptDir 'website_buildings.json'
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "website_buildings.json not found in $ScriptDir"
}

$all = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$cfg = $null
foreach ($prop in $all.PSObject.Properties) {
    if ($prop.Name -eq $CardId) {
        $cfg = $prop.Value
        break
    }
}
if (-not $cfg) {
    throw "Missing CardId in website_buildings.json: $CardId"
}

$buildingId = [string]$cfg.buildingId
$histYear = [string]$cfg.historicalPhotoYear
$modYear = [string]$cfg.modernPhotoYear
if (-not $modYear) { $modYear = (Get-Date).Year.ToString() }

function Escape-Regex([string]$s) {
    return [regex]::Escape($s)
}

# --- archiviewAssets.ts ---
$assetsFile = Join-Path $RepoRoot 'src\data\explorer\archiviewAssets.ts'

$explorerDir = Join-Path $RepoRoot ("public\explorer\{0}" -f $CardId)
$hasSideBySide = $false
$annPath = Join-Path $explorerDir 'annotations.json'
if (Test-Path -LiteralPath $annPath) {
    try {
        $annData = Get-Content -LiteralPath $annPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ([string]$annData.labeling_layout -eq 'side_by_side') {
            $hasSideBySide = $true
        }
    } catch { }
}
if (-not $hasSideBySide) {
    $hasSideBySide = Test-Path -LiteralPath (Join-Path $explorerDir 'side-by-side-marked.png')
}

$histLine = if ($histYear) { "    historicalPhotoYear: '$histYear'," } else { $null }
$markedUrlLine = if ($hasSideBySide) {
    ('    markedFacadeUrl: `${base}explorer/{0}/side-by-side-marked.png`,' -f $CardId)
} else {
    ('    markedFacadeUrl: `${base}explorer/{0}/marked-facade.png`,' -f $CardId)
}
$entryLines = @(
    "  ${buildingId}: {"
    "    buildingId: '$buildingId',"
    "    cardId: '$CardId',"
    $markedUrlLine
    ('    labeledFacadeUrl: `${base}explorer/{0}/marked-facade-labeled.png`,' -f $CardId)
)
if ($hasSideBySide) {
    $entryLines += ('    sideBySideMarkedUrl: `${base}explorer/{0}/side-by-side-marked.png`,' -f $CardId)
    $entryLines += "    labelingLayout: 'side_by_side',"
}
$entryLines += @(
    ('    historicalRectifiedUrl: `${base}explorer/{0}/historical-rectified.png`,' -f $CardId)
    ('    modernRectifiedUrl: `${base}explorer/{0}/modern-rectified.png`,' -f $CardId)
)
if ($histLine) { $entryLines += $histLine }
$entryLines += @(
    "    modernPhotoYear: '$modYear',"
    ('    annotationsUrl: `${base}explorer/{0}/annotations.json`,' -f $CardId)
    ('    facadeProjectUrl: `${base}explorer/{0}/facade-project.json`,' -f $CardId)
    '  },'
)
$entry = $entryLines -join "`n"

$content = Get-Content -LiteralPath $assetsFile -Raw -Encoding UTF8
$idPattern = "(?ms)^  $(Escape-Regex $buildingId): \{.*?\r?\n  \},\r?\n"
if ([regex]::IsMatch($content, $idPattern)) {
    $content = [regex]::Replace($content, $idPattern, "$entry`n")
} else {
    $content = [regex]::Replace(
        $content,
        '(?ms)(export const ARCHIVIEW_ASSETS[^{]+\{\r?\n)',
        "`$1$entry`n"
    )
}
Set-Content -LiteralPath $assetsFile -Value $content -Encoding UTF8 -NoNewline
Write-Host "OK: archiviewAssets.ts -> $buildingId"

try {
# --- moscow00X.ts verification ---
$num = $CardId -replace '^MOSCOW_', ''
$buildingFile = Join-Path $RepoRoot ("src\data\buildings\moscow{0}.ts" -f $num.ToLower())
if (-not (Test-Path -LiteralPath $buildingFile)) {
    Write-Host "SKIP: building file not found: $buildingFile"
} else {

$expertiseBlock = ''
if ($cfg.officialExpertise -and $cfg.officialExpertise.url) {
    $t = [string]$cfg.officialExpertise.title -replace "'", "\'"
    $u = [string]$cfg.officialExpertise.url
    $issued = [string]$cfg.officialExpertise.issuedAt
    $issuedLine = if ($issued) { "        issuedAt: '$issued'," } else { '' }
    $expertiseBlock = @(
        '    officialExpertise: ['
        '      {'
        "        title: '$t',"
        "        url: '$u',"
        $issuedLine
        '      },'
        '    ],'
    ) -join "`n"
    if ($issuedLine) { $expertiseBlock += "`n" }
}

$histYearProp = if ($histYear) { "    historicalPhotoYear: '$histYear'," } else { $null }
$verificationLines = @(
    '  verification: {'
    '    historicalPhoto: true,'
)
if ($histYearProp) { $verificationLines += $histYearProp }
$verificationLines += "    modernPhotoYear: '$modYear',"
if ($expertiseBlock) { $verificationLines += $expertiseBlock }
$verificationLines += '  },'
$verificationBlock = $verificationLines -join "`n"

$bContent = Get-Content -LiteralPath $buildingFile -Raw -Encoding UTF8
$verPattern = '(?ms)^  verification: \{.*?\r?\n  \},\r?\n'
if ([regex]::IsMatch($bContent, $verPattern)) {
    $bContent = [regex]::Replace($bContent, $verPattern, "$verificationBlock`n")
    Write-Host "OK: updated verification in $(Split-Path $buildingFile -Leaf)"
} elseif ($bContent -match '(?ms)  summary:\r?\n') {
    $bContent = [regex]::Replace($bContent, '(?ms)(  summary:\r?\n)', "`$1$verificationBlock`n", 1)
    Write-Host "OK: added verification block in $(Split-Path $buildingFile -Leaf)"
} else {
    Write-Host "SKIP: could not insert verification block"
}

Set-Content -LiteralPath $buildingFile -Value $bContent -Encoding UTF8 -NoNewline
}
} catch {
    Write-Host "WARN: moscow*.ts verification skipped: $_"
}

$notePath = Join-Path $RepoRoot ("public\explorer\{0}\NEXT_STEPS.txt" -f $CardId)
$noteDir = Split-Path $notePath -Parent
if (-not (Test-Path -LiteralPath $noteDir)) {
    New-Item -ItemType Directory -Path $noteDir -Force | Out-Null
}
@(
    'Archiview export copied to public/explorer.',
    'Updated: archiviewAssets.ts',
    '',
    'Next: GitHub Desktop -> Commit -> Push -> Ctrl+F5 on site.'
) | Set-Content -LiteralPath $notePath -Encoding UTF8
Write-Host "OK: $notePath"
