import { polygonAreaAbs, polygonCentroid, type Point } from './archiviewGeometry'

/** Площадь в %²: крупная зона — номер по центру; мелкие и средние — выноска у края. */
const BADGE_ON_REGION_AREA = 12

const BADGE_COLLISION_RADIUS = 2.85

export type BadgeLayout = {
  anchorX: number
  anchorY: number
  badgeX: number
  badgeY: number
  callout: boolean
}

type PlacementSide = 'below' | 'above' | 'left' | 'right' | 'topLeft' | 'topRight'

type BBox = { minX: number; minY: number; maxX: number; maxY: number }

/** Доп. сдвиг кружка после базовой позиции у края (дом со зверями). */
const MOSCOW_003_BADGE_NUDGE: Record<number, { dx: number; dy: number }> = {
  5: { dx: -2.2, dy: 3.4 },
  13: { dx: -0.8, dy: 5.2 },
  14: { dx: 0.6, dy: 7.8 },
  9: { dx: -2.4, dy: -0.6 },
  7: { dx: -1.4, dy: 1.0 },
  8: { dx: 1.0, dy: 1.6 },
  1: { dx: -0.6, dy: -0.5 },
  2: { dx: 1.2, dy: 0 },
}

/** Дом со зверями: предпочтительная сторона кружка относительно зоны. */
const MOSCOW_003_BADGE_SIDE: Record<number, PlacementSide> = {
  1: 'topLeft',
  2: 'right',
  3: 'below',
  4: 'below',
  5: 'below',
  7: 'below',
  8: 'below',
  9: 'below',
  13: 'below',
  14: 'below',
}

function clampPct(value: number): number {
  return Math.min(97, Math.max(3, value))
}

function polygonBBox(points: Point[]): BBox {
  const xs = points.map((p) => p[0])
  const ys = points.map((p) => p[1])
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  }
}

function badgeMargin(bbox: BBox): number {
  const span = Math.max(bbox.maxX - bbox.minX, bbox.maxY - bbox.minY)
  return Math.max(2.4, Math.min(4.2, span * 0.55 + 1.8))
}

function layoutOnSide(
  polygon: Point[],
  area: number,
  side: PlacementSide,
  idx = 0,
): BadgeLayout {
  const bbox = polygonBBox(polygon)
  const margin = badgeMargin(bbox)
  const midX = (bbox.minX + bbox.maxX) / 2
  const midY = (bbox.minY + bbox.maxY) / 2

  let badgeX = midX
  let badgeY = midY
  switch (side) {
    case 'below':
      badgeX = midX
      badgeY = bbox.maxY + margin
      break
    case 'above':
      badgeX = midX
      badgeY = bbox.minY - margin
      break
    case 'left':
      badgeX = bbox.minX - margin
      badgeY = midY
      break
    case 'right':
      badgeX = bbox.maxX + margin
      badgeY = midY
      break
    case 'topLeft':
      badgeX = bbox.minX - margin * 0.55
      badgeY = bbox.minY - margin * 0.55
      break
    case 'topRight':
      badgeX = bbox.maxX + margin * 0.55
      badgeY = bbox.minY - margin * 0.55
      break
  }

  const nudge = MOSCOW_003_BADGE_NUDGE[idx]
  if (nudge) {
    badgeX += nudge.dx
    badgeY += nudge.dy
  }

  return {
    anchorX: midX,
    anchorY: midY,
    badgeX: clampPct(badgeX),
    badgeY: clampPct(badgeY),
    callout: area < BADGE_ON_REGION_AREA,
  }
}

function defaultSideOrder(polygon: Point[]): PlacementSide[] {
  const bbox = polygonBBox(polygon)
  const midY = (bbox.minY + bbox.maxY) / 2
  const midX = (bbox.minX + bbox.maxX) / 2

  if (midY < 54) {
    if (midX < 30) return ['below', 'left', 'right', 'above', 'topLeft', 'topRight']
    if (midX > 68) return ['below', 'right', 'left', 'above', 'topRight', 'topLeft']
    return ['below', 'left', 'right', 'above', 'topLeft', 'topRight']
  }
  if (midY > 62) return ['above', 'left', 'right', 'below', 'topLeft', 'topRight']
  return ['left', 'right', 'below', 'above', 'topLeft', 'topRight']
}

function candidateLayouts(polygon: Point[], area: number, idx: number): BadgeLayout[] {
  const preferred = MOSCOW_003_BADGE_SIDE[idx]
  const sides = preferred
    ? [preferred, ...defaultSideOrder(polygon).filter((side) => side !== preferred)]
    : defaultSideOrder(polygon)

  const seen = new Set<string>()
  const layouts: BadgeLayout[] = []
  for (const side of sides) {
    const layout = layoutOnSide(polygon, area, side, idx)
    const key = `${layout.badgeX.toFixed(1)}:${layout.badgeY.toFixed(1)}`
    if (seen.has(key)) continue
    seen.add(key)
    layouts.push(layout)
  }
  return layouts
}

function badgesOverlap(a: BadgeLayout, b: BadgeLayout): boolean {
  const dx = a.badgeX - b.badgeX
  const dy = a.badgeY - b.badgeY
  const minDist = BADGE_COLLISION_RADIUS * 2
  return dx * dx + dy * dy < minDist * minDist
}

function layoutScore(layout: BadgeLayout, idx: number, order: number): number {
  const lineLen =
    (layout.badgeX - layout.anchorX) ** 2 + (layout.badgeY - layout.anchorY) ** 2
  const edgePenalty = layout.badgeY < 8 ? 40 : layout.badgeY > 94 ? 25 : 0
  const preferred = MOSCOW_003_BADGE_SIDE[idx]
  const preferredBonus =
    preferred === 'below' && layout.badgeY > layout.anchorY
      ? -8
      : preferred === 'topLeft' &&
          layout.badgeX < layout.anchorX &&
          layout.badgeY < layout.anchorY
        ? -8
        : preferred === 'right' && layout.badgeX > layout.anchorX
          ? -8
          : 0
  return lineLen + edgePenalty + preferredBonus + order * 0.15
}

function nudgeLayout(layout: BadgeLayout, attempt: number, idx: number): BadgeLayout {
  const preferred = MOSCOW_003_BADGE_SIDE[idx]
  if (preferred === 'below') {
    return {
      ...layout,
      badgeX: clampPct(layout.badgeX + (attempt % 2 === 1 ? (idx % 2 ? 2.2 : -2.2) : 0)),
      badgeY: clampPct(layout.badgeY + 2.2 + attempt * 1.6),
    }
  }
  if (preferred === 'above') {
    return {
      ...layout,
      badgeX: clampPct(layout.badgeX + (attempt % 2 === 1 ? (idx % 2 ? 2.2 : -2.2) : 0)),
      badgeY: clampPct(layout.badgeY - 2.2 - attempt * 1.6),
    }
  }
  const angle = ((idx * 47 + attempt * 53) % 360) * (Math.PI / 180)
  const radius = 2.4 + attempt * 1.6
  return {
    ...layout,
    badgeX: clampPct(layout.badgeX + Math.cos(angle) * radius),
    badgeY: clampPct(layout.badgeY + Math.sin(angle) * radius),
  }
}

/**
 * Крупная зона — номер по центру; мелкая — выносной кружок у края полигона.
 */
export function computeBadgeLayout(polygonPct: Point[], areaPct?: number, idx?: number): BadgeLayout {
  const area = areaPct ?? polygonAreaAbs(polygonPct)
  const [cx, cy] = polygonCentroid(polygonPct)

  if (area >= BADGE_ON_REGION_AREA) {
    return { anchorX: cx, anchorY: cy, badgeX: cx, badgeY: cy, callout: false }
  }

  const candidates = candidateLayouts(polygonPct, area, idx ?? 0)
  return candidates[0] ?? layoutOnSide(polygonPct, area, 'below', idx ?? 0)
}

type RegionForBadgeLayout = {
  idx: number
  polygonPct: Point[]
  areaPct: number
  badgeLayout: BadgeLayout
}

/** Разводит кружки, чтобы не перекрывали друг друга (сначала мелкие зоны). */
export function assignBadgeLayouts(regions: RegionForBadgeLayout[]): void {
  const placed: BadgeLayout[] = []
  const sorted = [...regions].sort((a, b) => a.areaPct - b.areaPct)

  for (const region of sorted) {
    if (region.areaPct >= BADGE_ON_REGION_AREA) {
      const centered: BadgeLayout = {
        anchorX: region.badgeLayout.anchorX,
        anchorY: region.badgeLayout.anchorY,
        badgeX: region.badgeLayout.anchorX,
        badgeY: region.badgeLayout.anchorY,
        callout: false,
      }
      region.badgeLayout = centered
      placed.push(centered)
      continue
    }

    const candidates = candidateLayouts(region.polygonPct, region.areaPct, region.idx)
    let chosen: BadgeLayout | null = null
    let bestScore = Number.POSITIVE_INFINITY

    candidates.forEach((candidate, order) => {
      if (placed.some((other) => badgesOverlap(candidate, other))) return
      const score = layoutScore(candidate, region.idx, order)
      if (score < bestScore) {
        bestScore = score
        chosen = candidate
      }
    })

    if (!chosen) {
      const seed = candidates[0] ?? computeBadgeLayout(region.polygonPct, region.areaPct, region.idx)
      chosen = seed
      for (let attempt = 0; attempt < 24; attempt += 1) {
        const nudged = nudgeLayout(seed, attempt, region.idx)
        if (!placed.some((other) => badgesOverlap(nudged, other))) {
          chosen = nudged
          break
        }
      }
    }

    region.badgeLayout = chosen
    placed.push(chosen)
  }
}
