param(
    [Parameter(Mandatory = $true)][string]$ProjectJson,
    [Parameter(Mandatory = $true)][string]$OutJson
)
$p = Get-Content -LiteralPath $ProjectJson -Raw -Encoding UTF8 | ConvertFrom-Json
$out = [ordered]@{
    H_rect_to_modern       = $p.H_rect_to_modern
    labeling_layout        = $p.labeling_layout
    side_by_side           = $p.side_by_side
    rectified_size         = $p.rectified_size
    modern_crop_offset_xy  = $p.modern_crop_offset_xy
    modern_crop_rect_text  = $p.modern_crop_rect_text
}
if ($p.H_rect_to_ar) { $out.H_rect_to_ar = $p.H_rect_to_ar }
$out | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutJson -Encoding UTF8
