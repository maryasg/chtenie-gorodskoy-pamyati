param(
    [Parameter(Mandatory = $true)][string]$ProjectJson,
    [Parameter(Mandatory = $true)][string]$OutJson
)
$p = Get-Content -LiteralPath $ProjectJson -Raw -Encoding UTF8 | ConvertFrom-Json
@{ H_rect_to_modern = $p.H_rect_to_modern } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutJson -Encoding UTF8
