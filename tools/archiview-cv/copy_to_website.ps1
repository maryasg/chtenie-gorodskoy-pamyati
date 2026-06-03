# Copy Archiview export to website. Run copy_to_website.bat
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Web = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\public\explorer\MOSCOW_003'
$ProjectId = '20260520_190036'

function Find-ResultFolder {
    param([string]$StartDir)
    $direct = Join-Path $StartDir "archiview_projects\$ProjectId\result"
    if (Test-Path -LiteralPath $direct) { return $direct }

    $cultTech = Join-Path $env:USERPROFILE 'Desktop\Cult Tech'
    if (-not (Test-Path -LiteralPath $cultTech)) { return $null }

    $matches = Get-ChildItem -LiteralPath $cultTech -Recurse -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq 'result' -and $_.Parent.Name -eq $ProjectId } |
        Select-Object -First 1

    if ($matches) { return $matches.FullName }
    return $null
}

$Result = Find-ResultFolder -StartDir $ScriptDir

Write-Host ''
Write-Host 'FROM (Archiview result):'
if ($Result) { Write-Host "  $Result" } else { Write-Host '  NOT FOUND' }
Write-Host 'TO (website folder):'
Write-Host "  $Web"
Write-Host ''

if (-not $Result) {
    Write-Host 'ERROR: result folder not found.'
    Write-Host 'Run copy_to_website.bat from archiview v15 folder on Desktop.'
    Read-Host 'Press Enter to close'
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
Write-Host 'Done. Next: GitHub Desktop - Commit - Push'
Read-Host 'Press Enter to close'
