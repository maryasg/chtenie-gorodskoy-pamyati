$ErrorActionPreference = 'Stop'
$RepoRoot = 'C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati'
$patterns = @('archiview_cv_easy_v16_package', 'archiview_cv_easy_v15_package')
$v15 = $null
foreach ($pattern in $patterns) {
    $hits = Get-ChildItem -Path (Join-Path $env:USERPROFILE 'Desktop\Cult Tech') -Recurse -Directory -Filter $pattern -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($hits) { $v15 = $hits; break }
}
if (-not $v15) { throw 'archiview_cv_easy_v16_package or v15_package not found' }
$script = Join-Path $v15.FullName 'copy_to_website.ps1'
& $script -CardId MOSCOW_001 -RepoRoot $RepoRoot -NoPrompt
