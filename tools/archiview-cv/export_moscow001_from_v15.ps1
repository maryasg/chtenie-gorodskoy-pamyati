$ErrorActionPreference = 'Stop'
$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati'
$v15 = Get-ChildItem -Path (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter 'archiview_cv_easy_v15_package' -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $v15) { throw 'archiview_cv_easy_v15_package not found' }
$script = Join-Path $v15.FullName 'copy_to_website.ps1'
& $script -CardId MOSCOW_001 -RepoRoot $RepoRoot -NoPrompt
