export type Point = [number, number]

/** Перенос полигона из координат выпрямленного холста на исходное современное фото. */
export function transformPolygon(H: number[][], polygon: Point[]): Point[] {
  return polygon.map(([x, y]) => {
    const w = H[2][0] * x + H[2][1] * y + H[2][2]
    if (Math.abs(w) < 1e-12) return [x, y]
    return [
      (H[0][0] * x + H[0][1] * y + H[0][2]) / w,
      (H[1][0] * x + H[1][1] * y + H[1][2]) / w,
    ]
  })
}

export function polygonCentroid(points: Point[]): Point {
  if (points.length === 0) return [50, 50]
  const xs = points.map((p) => p[0])
  const ys = points.map((p) => p[1])
  return [xs.reduce((a, b) => a + b, 0) / xs.length, ys.reduce((a, b) => a + b, 0) / ys.length]
}

export function toPercentPoints(points: Point[], width: number, height: number): Point[] {
  return points.map(([x, y]) => [(x / width) * 100, (y / height) * 100])
}

type SideBySideMeta = {
  label_bar_height?: number
  panel_height?: number
  modern_offset_x?: number
  historical_crop_size?: [number, number]
  modern_crop_size?: [number, number]
}

/** Координаты разметки на панели «история | современность». */
export function rectifiedPolygonToComparison(
  polygon: Point[],
  side: 'historical' | 'modern',
  sb: SideBySideMeta,
  rectifiedSize?: { width?: number; height?: number },
): Point[] {
  const labelH = Number(sb.label_bar_height ?? 0)
  let panelH = Number(sb.panel_height ?? 0)
  if (panelH <= 0 && rectifiedSize?.height) {
    panelH = Number(rectifiedSize.height) - labelH
  }
  const cropSize = side === 'historical' ? sb.historical_crop_size : sb.modern_crop_size
  const ch = cropSize?.[1] ?? 0
  if (panelH <= 0 || ch <= 0) return polygon
  const scale = panelH / ch
  const modernX = Number(sb.modern_offset_x ?? 0)
  return polygon.map(([x, y]) => [
    x * scale + (side === 'modern' ? modernX : 0),
    y * scale + labelH,
  ])
}
