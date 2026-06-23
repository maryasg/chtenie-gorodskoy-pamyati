export type Point = [number, number]

type FacadeProjectCrop = {
  modern_crop_offset_xy?: [number, number]
  modern_crop_rect_text?: string
}

/** Сдвиг обрезки исходника: выпрямление → полный файл modern_image. */
export function sourceCropOffsetFromProject(project?: FacadeProjectCrop | null): Point {
  const off = project?.modern_crop_offset_xy
  if (Array.isArray(off) && off.length >= 2) {
    return [Number(off[0]) || 0, Number(off[1]) || 0]
  }
  const text = String(project?.modern_crop_rect_text ?? '').trim()
  if (!text) return [0, 0]
  const parts = text.replace(/\s+/g, '').split(',')
  if (parts.length !== 4) return [0, 0]
  const nums = parts.map((part) => Number(part))
  if (nums.some((n) => !Number.isFinite(n))) return [0, 0]
  const [x0, y0] = nums
  return [x0, y0]
}

/** Разметка в выпрямленном кадре → координаты полного исходного фото. */
export function homographyRectToFullSource(H_rect_to_cropped: number[][], cropOffset: Point): number[][] {
  const [dx, dy] = cropOffset
  if (Math.abs(dx) < 1e-9 && Math.abs(dy) < 1e-9) return H_rect_to_cropped
  return [
    [H_rect_to_cropped[0][0], H_rect_to_cropped[0][1], H_rect_to_cropped[0][2] + dx],
    [H_rect_to_cropped[1][0], H_rect_to_cropped[1][1], H_rect_to_cropped[1][2] + dy],
    H_rect_to_cropped[2],
  ]
}

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

/** Absolute polygon area (shoelace). Used to stack small regions above large overlaps for clicks. */
export function polygonAreaAbs(points: Point[]): number {
  if (points.length < 3) return 0
  let area = 0
  for (let i = 0; i < points.length; i++) {
    const [x1, y1] = points[i]
    const [x2, y2] = points[(i + 1) % points.length]
    area += x1 * y2 - x2 * y1
  }
  return Math.abs(area) / 2
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
