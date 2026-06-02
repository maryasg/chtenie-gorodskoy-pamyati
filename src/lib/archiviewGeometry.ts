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
