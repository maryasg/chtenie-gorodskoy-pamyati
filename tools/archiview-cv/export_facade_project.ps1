param(
    [Parameter(Mandatory = $true)][string]$ProjectJson,
    [Parameter(Mandatory = $true)][string]$OutJson
)
$p = Get-Content -LiteralPath $ProjectJson -Raw -Encoding UTF8 | ConvertFrom-Json
@{
    H_rect_to_modern = $p.H_rect_to_modern
    labeling_layout  = $p.labeling_layout
    side_by_side     = $p.side_by_side
    rectified_size   = $p.rectified_size
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutJson -Encoding UTF8
