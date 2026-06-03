param(
    [Parameter(Mandatory = $true)][string]$CardId,
    [Parameter(Mandatory = $true)][string]$RepoRoot,
    [string]$ScriptDir = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

$configPath = Join-Path $ScriptDir 'website_buildings.json'
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Не найден website_buildings.json в $ScriptDir"
}

$all = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$cfg = $all.$CardId
if (-not $cfg) {
    throw "В website_buildings.json нет записи для $CardId. Добавьте блок вручную один раз."
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

$entry = @(
    "  ${buildingId}: {"
    "    buildingId: '$buildingId',"
    "    cardId: '$CardId',"
    "    markedFacadeUrl: `` `$`{base}explorer/$CardId/marked-facade.png``,"
    "    labeledFacadeUrl: `` `$`{base}explorer/$CardId/marked-facade-labeled.png``,"
    "    historicalRectifiedUrl: `` `$`{base}explorer/$CardId/historical-rectified.png``,"
    "    modernRectifiedUrl: `` `$`{base}explorer/$CardId/modern-rectified.png``,"
    $(if ($histYear) { "    historicalPhotoYear: '$histYear'," })
    "    modernPhotoYear: '$modYear',"
    "    annotationsUrl: `` `$`{base}explorer/$CardId/annotations.json``,"
    "    facadeProjectUrl: `` `$`{base}explorer/$CardId/facade-project.json``,"
    "  },"
) -join "`n"

$content = Get-Content -LiteralPath $assetsFile -Raw -Encoding UTF8
$idPattern = "(?ms)^  $(Escape-Regex $buildingId): \{.*?\r?\n  \},\r?\n"
if ([regex]::IsMatch($content, $idPattern)) {
    $content = [regex]::Replace($content, $idPattern, "$entry`n")
} else {
    $content = [regex]::Replace(
        $content,
        '(?ms)(export const ARCHIVIEW_ASSETS[^\{]+\{\r?\n)',
        "`$1$entry`n"
    )
}
Set-Content -LiteralPath $assetsFile -Value $content -Encoding UTF8 -NoNewline
Write-Host "OK: archiviewAssets.ts -> $buildingId"

# --- moscow00X.ts verification ---
$num = $CardId -replace '^MOSCOW_', ''
$buildingFile = Join-Path $RepoRoot ("src\data\buildings\moscow{0}.ts" -f $num.ToLower())
if (-not (Test-Path -LiteralPath $buildingFile)) {
    Write-Host "SKIP: нет файла $buildingFile"
    return
}

$expertiseBlock = ''
if ($cfg.officialExpertise -and $cfg.officialExpertise.url) {
    $t = [string]$cfg.officialExpertise.title -replace "'", "\'"
    $u = [string]$cfg.officialExpertise.url
    $issued = [string]$cfg.officialExpertise.issuedAt
    $issuedLine = if ($issued) { "`n        issuedAt: '$issued'," } else { '' }
    $expertiseBlock = @"
    officialExpertise: [
      {
        title: '$t',
        url: '$u',$issuedLine
      },
    ],
"@
}

$histYearProp = if ($histYear) { "    historicalPhotoYear: '$histYear',`n" } else { '' }
$verificationBlock = @"
  verification: {
    historicalPhoto: true,
${histYearProp}    modernPhotoYear: '$modYear',
$expertiseBlock  },
"@

$bContent = Get-Content -LiteralPath $buildingFile -Raw -Encoding UTF8
$verPattern = '(?ms)^  verification: \{.*?\r?\n  \},\r?\n'
if ([regex]::IsMatch($bContent, $verPattern)) {
    $bContent = [regex]::Replace($bContent, $verPattern, "$verificationBlock`n")
    Write-Host "OK: обновлён блок verification в $(Split-Path $buildingFile -Leaf)"
} elseif ($bContent -match '(?ms)(  summary:\r?\n    ''[^'']+'',\r?\n)') {
    $bContent = [regex]::Replace($bContent, '(?ms)(  summary:\r?\n    ''[^'']+'',\r?\n)', "`$1$verificationBlock`n")
    Write-Host "OK: добавлен блок verification в $(Split-Path $buildingFile -Leaf)"
} else {
    Write-Host "SKIP: не удалось вставить verification — откройте файл вручную"
}

Set-Content -LiteralPath $buildingFile -Value $bContent -Encoding UTF8 -NoNewline

$notePath = Join-Path $RepoRoot ("public\explorer\{0}\NEXT_STEPS.txt" -f $CardId)
$noteDir = Split-Path $notePath -Parent
if (-not (Test-Path -LiteralPath $noteDir)) {
    New-Item -ItemType Directory -Path $noteDir -Force | Out-Null
}
@(
    "Экспорт Archiview -> сайт выполнен автоматически.",
    "Обновлено: archiviewAssets.ts, verification в moscow$($num.ToLower()).ts (если было в website_buildings.json).",
    "",
    "Дальше: GitHub Desktop -> Commit -> Push origin -> Ctrl+F5 на сайте.",
    "",
    "Если PDF экспертизы ещё нет в website_buildings.json — добавьте один раз в:",
    "  tools/archiview-cv/website_buildings.json"
) | Set-Content -LiteralPath $notePath -Encoding UTF8
Write-Host "OK: $notePath"
