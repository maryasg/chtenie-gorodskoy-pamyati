import { polygonAreaAbs, polygonCentroid, type Point } from './archiviewGeometry'

/** Площадь в %²: крупная зона — номер по центру; мелкие и средние — выноска у края. */
const BADGE_ON_REGION_AREA = 12

const BADGE_COLLISION_RADIUS = 2.15

export type BadgeLayout = {
  anchorX: number
  anchorY: number
  badgeX: number
  badgeY: number
  callout: boolean
}

type PlacementSide = 'below' | 'above' | 'left' | 'right' | 'topLeft' | 'topRight'

type BBox = { minX: number; minY: number; maxX: number; maxY: number }

type CardBadgePrefs = {
  /** Все номера — выносные кружки у края зоны, не по центру (даже у крупной надстройки). */
  alwaysCallout?: boolean
  collisionRadius?: number
  side?: Record<number, PlacementSide>
  nudge?: Record<number, { dx: number; dy: number }>
}

/** Дом со зверями: тонкая подстройка у края зоны (без «отлёта»). */
const MOSCOW_003_PREFS: CardBadgePrefs = {
  nudge: {
    1: { dx: -0.8, dy: -0.4 },
    2: { dx: 0.8, dy: 0 },
    3: { dx: -0.4, dy: 0.2 },
    4: { dx: 0.3, dy: 0.2 },
    5: { dx: -0.6, dy: 0.4 },
    7: { dx: -1.0, dy: 0 },
    8: { dx: -0.8, dy: 0.2 },
    9: { dx: -1.2, dy: 0.5 },
    10: { dx: 0, dy: -0.4 },
    11: { dx: 0.2, dy: -0.4 },
    13: { dx: 0.2, dy: 0.6 },
    14: { dx: -1.0, dy: 0.2 },
  },
  side: {
    1: 'topLeft',
    2: 'right',
    3: 'below',
    4: 'below',
    5: 'below',
    7: 'left',
    8: 'left',
    9: 'below',
    10: 'below',
    11: 'below',
    13: 'below',
    14: 'left',
  },
}

/** Дом Ардовых / Куманиных: кружки с номерами рядом с зоной, не на подсветке. */
const MOSCOW_001_PREFS: CardBadgePrefs = {
  alwaysCallout: true,
  collisionRadius: 2.65,
  side: {
    1: 'above',
    2: 'left',
    3: 'topRight',
    4: 'right',
    5: 'left',
    6: 'below',
    7: 'topLeft',
    8: 'below',
    9: 'left',
    10: 'right',
    11: 'below',
  },
  nudge: {
    1: { dx: 0, dy: -1.4 },
    2: { dx: -1.6, dy: 0 },
    3: { dx: 1.8, dy: -2.2 },
    4: { dx: 2.4, dy: -0.6 },
    5: { dx: -2.6, dy: 0.3 },
    6: { dx: 0.8, dy: 1.2 },
    7: { dx: -2.0, dy: -1.5 },
    8: { dx: 0, dy: 1.1 },
    9: { dx: -2.0, dy: -0.5 },
    10: { dx: 2.2, dy: -1.4 },
    11: { dx: 0, dy: 1.3 },
  },
}

const CARD_BADGE_PREFS: Record<string, CardBadgePrefs> = {
  MOSCOW_001: MOSCOW_001_PREFS,
  MOSCOW_003: MOSCOW_003_PREFS,
}

function prefsForCard(cardId?: string): CardBadgePrefs {
  if (!cardId) return {}
  return CARD_BADGE_PREFS[cardId] ?? {}
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
  return Math.max(0.85, Math.min(1.7, span * 0.18 + 0.55))
}

function layoutOnSide(
  polygon: Point[],
  area: number,
  side: PlacementSide,
  idx = 0,
  cardId?: string,
): BadgeLayout {
  const { nudge: nudgeMap } = prefsForCard(cardId)
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
      badgeX = bbox.minX - margin * 0.45
      badgeY = bbox.minY - margin * 0.45
      break
    case 'topRight':
      badgeX = bbox.maxX + margin * 0.45
      badgeY = bbox.minY - margin * 0.45
      break
  }

  const nudge = nudgeMap?.[idx]
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
    if (midX < 30) return ['left', 'below', 'above', 'right', 'topLeft', 'topRight']
    if (midX > 68) return ['left', 'below', 'right', 'above', 'topRight', 'topLeft']
    return ['below', 'left', 'right', 'above', 'topLeft', 'topRight']
  }
  if (midY > 62) return ['above', 'left', 'right', 'below', 'topLeft', 'topRight']
  return ['left', 'right', 'below', 'above', 'topLeft', 'topRight']
}

function candidateLayouts(
  polygon: Point[],
  area: number,
  idx: number,
  cardId?: string,
): BadgeLayout[] {
  const { side: sideMap } = prefsForCard(cardId)
  const preferred = sideMap?.[idx]
  const sides = preferred
    ? [preferred, ...defaultSideOrder(polygon).filter((side) => side !== preferred)]
    : defaultSideOrder(polygon)

  const seen = new Set<string>()
  const layouts: BadgeLayout[] = []
  for (const side of sides) {
    const layout = layoutOnSide(polygon, area, side, idx, cardId)
    const key = `${layout.badgeX.toFixed(1)}:${layout.badgeY.toFixed(1)}`
    if (seen.has(key)) continue
    seen.add(key)
    layouts.push(layout)
  }
  return layouts
}

function badgesOverlap(a: BadgeLayout, b: BadgeLayout, cardId?: string): boolean {
  const { collisionRadius } = prefsForCard(cardId)
  const radius = collisionRadius ?? BADGE_COLLISION_RADIUS
  const dx = a.badgeX - b.badgeX
  const dy = a.badgeY - b.badgeY
  const minDist = radius * 2
  return dx * dx + dy * dy < minDist * minDist
}

function layoutScore(layout: BadgeLayout, idx: number, order: number, cardId?: string): number {
  const { side: sideMap } = prefsForCard(cardId)
  const lineLen =
    (layout.badgeX - layout.anchorX) ** 2 + (layout.badgeY - layout.anchorY) ** 2
  const edgePenalty = layout.badgeY < 8 ? 40 : layout.badgeY > 94 ? 25 : 0
  const preferred = sideMap?.[idx]
  const preferredBonus =
    preferred === 'below' && layout.badgeY > layout.anchorY
      ? -12
      : preferred === 'above' && layout.badgeY < layout.anchorY
        ? -12
        : preferred === 'left' && layout.badgeX < layout.anchorX
          ? -12
          : preferred === 'topLeft' &&
              layout.badgeX < layout.anchorX &&
              layout.badgeY < layout.anchorY
            ? -12
            : preferred === 'right' && layout.badgeX > layout.anchorX
              ? -12
              : 0
  return lineLen * 14 + edgePenalty + preferredBonus + order * 0.2
}

function nudgeLayout(layout: BadgeLayout, attempt: number, idx: number, cardId?: string): BadgeLayout {
  const { side: sideMap } = prefsForCard(cardId)
  const preferred = sideMap?.[idx]
  if (preferred === 'below') {
    return {
      ...layout,
      badgeX: clampPct(layout.badgeX + (attempt % 2 === 1 ? 1.2 : -1.2)),
      badgeY: clampPct(layout.badgeY + attempt * 0.65),
    }
  }
  if (preferred === 'left') {
    return {
      ...layout,
      badgeX: clampPct(layout.badgeX - attempt * 0.55),
      badgeY: clampPct(layout.badgeY + (attempt % 2 === 1 ? 0.9 : -0.9)),
    }
  }
  if (preferred === 'above') {
    return {
      ...layout,
      badgeX: clampPct(layout.badgeX + (attempt % 2 === 1 ? 1.2 : -1.2)),
      badgeY: clampPct(layout.badgeY - attempt * 0.65),
    }
  }
  const angle = ((idx * 47 + attempt * 53) % 360) * (Math.PI / 180)
  const radius = 0.9 + attempt * 0.55
  return {
    ...layout,
    badgeX: clampPct(layout.badgeX + Math.cos(angle) * radius),
    badgeY: clampPct(layout.badgeY + Math.sin(angle) * radius),
  }
}

/**
 * Крупная зона — номер по центру; мелкая — выносной кружок у края полигона.
 */
export function computeBadgeLayout(
  polygonPct: Point[],
  areaPct?: number,
  idx?: number,
  cardId?: string,
): BadgeLayout {
  const area = areaPct ?? polygonAreaAbs(polygonPct)
  const [cx, cy] = polygonCentroid(polygonPct)
  const { alwaysCallout } = prefsForCard(cardId)

  if (area >= BADGE_ON_REGION_AREA && !alwaysCallout) {
    return { anchorX: cx, anchorY: cy, badgeX: cx, badgeY: cy, callout: false }
  }

  const candidates = candidateLayouts(polygonPct, area, idx ?? 0, cardId)
  return candidates[0] ?? layoutOnSide(polygonPct, area, 'below', idx ?? 0, cardId)
}

type RegionForBadgeLayout = {
  idx: number
  polygonPct: Point[]
  areaPct: number
  badgeLayout: BadgeLayout
}

/** Разводит кружки, чтобы не перекрывали друг друга (сначала мелкие зоны). */
export function assignBadgeLayouts(regions: RegionForBadgeLayout[], cardId?: string): void {
  const placed: BadgeLayout[] = []
  const sorted = [...regions].sort((a, b) => a.areaPct - b.areaPct)

  const { alwaysCallout } = prefsForCard(cardId)

  for (const region of sorted) {
    if (region.areaPct >= BADGE_ON_REGION_AREA && !alwaysCallout) {
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

    const candidates = candidateLayouts(region.polygonPct, region.areaPct, region.idx, cardId)
    let chosen: BadgeLayout | null = null
    let bestScore = Number.POSITIVE_INFINITY

    candidates.forEach((candidate, order) => {
      if (placed.some((other) => badgesOverlap(candidate, other, cardId))) return
      const score = layoutScore(candidate, region.idx, order, cardId)
      if (score < bestScore) {
        bestScore = score
        chosen = candidate
      }
    })

    if (!chosen) {
      const seed =
        candidates[0] ??
        computeBadgeLayout(region.polygonPct, region.areaPct, region.idx, cardId)
      chosen = seed
      for (let attempt = 0; attempt < 24; attempt += 1) {
        const nudged = nudgeLayout(seed, attempt, region.idx, cardId)
        if (!placed.some((other) => badgesOverlap(nudged, other, cardId))) {
          chosen = nudged
          break
        }
      }
    }

    region.badgeLayout = { ...chosen, callout: true }
    placed.push(chosen)
  }
}
