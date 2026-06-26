import { polygonAreaAbs, polygonCentroid, type Point } from './archiviewGeometry'

/** Площадь в %²: крупная зона — номер по центру; мелкие — выноска у края. */
const BADGE_ON_REGION_AREA = 12

/** Диаметр кружка в координатах фото (0–100). */
const BADGE_DIAMETER_PCT = 2.6

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
  collisionRadius?: number
  side?: Record<number, PlacementSide>
  nudge?: Record<number, { dx: number; dy: number }>
  /** Номер по центру подсветки (напр. крупные зоны 1 и 9 у Куманиных на телефоне). */
  forceOnRegion?: number[]
}

/** Дом Ардовых / Куманиных: предпочтительная сторона выноски. */
const MOSCOW_001_PREFS: CardBadgePrefs = {
  collisionRadius: 2.65,
  side: {
    1: 'above',
    2: 'left',
    3: 'right',
    4: 'right',
    5: 'above',
    6: 'above',
    7: 'topLeft',
    8: 'below',
    9: 'left',
    10: 'right',
    11: 'below',
  },
  nudge: {
    1: { dx: 0, dy: -1.4 },
    2: { dx: -1.6, dy: 0 },
    3: { dx: 0.35, dy: 0.05 },
    4: { dx: 2.4, dy: -0.6 },
    5: { dx: -0.2, dy: -0.45 },
    6: { dx: 0, dy: -0.5 },
    7: { dx: -2.0, dy: -1.5 },
    8: { dx: 0, dy: 1.1 },
    9: { dx: -2.0, dy: -0.5 },
    10: { dx: 2.2, dy: -1.4 },
    11: { dx: 0, dy: 1.3 },
  },
}

const CARD_BADGE_PREFS: Record<string, CardBadgePrefs> = {
  MOSCOW_001: MOSCOW_001_PREFS,
}

/** Второе сравнение Куманиных (1840→2026): номера над зоной, не на подсветке. */
const MOSCOW_001_CMP_009_PREFS: CardBadgePrefs = {
  collisionRadius: 2.4,
  side: { 1: 'above', 2: 'above', 3: 'above' },
  nudge: {
    1: { dx: 0, dy: -1.4 },
    2: { dx: -0.6, dy: -1.4 },
    3: { dx: 0.6, dy: -1.4 },
  },
}

/** Куманины cmp_005 на телефоне: номера у своих зон, не полосой внизу. */
const MOSCOW_001_CMP_005_MOBILE_PREFS: CardBadgePrefs = {
  collisionRadius: 2.65,
  forceOnRegion: [1, 9],
  side: {
    3: 'right',
    4: 'right',
    5: 'left',
    7: 'left',
  },
  nudge: {
    3: { dx: 0.35, dy: 0.05 },
    4: { dx: 2.4, dy: -0.6 },
    5: { dx: -1.6, dy: 0 },
    7: { dx: -2.0, dy: -1.5 },
  },
}

const COMPARISON_BADGE_PREFS: Record<string, CardBadgePrefs> = {
  'MOSCOW_001:cmp_009': MOSCOW_001_CMP_009_PREFS,
  'MOSCOW_001:cmp_008': {
    side: { 1: 'above', 2: 'above' },
    nudge: { 1: { dx: 0, dy: -1.4 }, 2: { dx: 0.6, dy: -1.4 } },
  },
  'MOSCOW_001:cmp_005:mobile': MOSCOW_001_CMP_005_MOBILE_PREFS,
}

function prefsForCard(cardId?: string, comparisonId?: string, mobile = false): CardBadgePrefs {
  if (cardId && comparisonId) {
    if (mobile) {
      const mobileKey = `${cardId}:${comparisonId}:mobile`
      if (COMPARISON_BADGE_PREFS[mobileKey]) return COMPARISON_BADGE_PREFS[mobileKey]
    }
    const comparisonKey = `${cardId}:${comparisonId}`
    if (COMPARISON_BADGE_PREFS[comparisonKey]) return COMPARISON_BADGE_PREFS[comparisonKey]
  }
  if (!cardId) return {}
  return CARD_BADGE_PREFS[cardId] ?? {}
}

/** Полоса номеров внизу кадра — не для Куманиных cmp_005. */
export function usesMobileBottomBadgeStrip(cardId?: string, comparisonId?: string): boolean {
  if (cardId === 'MOSCOW_001' && (!comparisonId || comparisonId === 'cmp_005')) return false
  return true
}

function badgesAlwaysOutside(cardId?: string, comparisonId?: string): boolean {
  return Boolean(
    cardId === 'MOSCOW_001' && comparisonId && (comparisonId === 'cmp_009' || comparisonId === 'cmp_008'),
  )
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

/** Ray-casting: точка внутри полигона. */
export function pointInPolygon(point: Point, polygon: Point[]): boolean {
  const [x, y] = point
  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i]
    const [xj, yj] = polygon[j]
    const intersects = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi
    if (intersects) inside = !inside
  }
  return inside
}

function regionFitsBadgeInside(bbox: BBox, area: number): boolean {
  const spanW = bbox.maxX - bbox.minX
  const spanH = bbox.maxY - bbox.minY
  const minSpan = Math.min(spanW, spanH)
  return area >= BADGE_ON_REGION_AREA && minSpan >= BADGE_DIAMETER_PCT * 1.1
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
  comparisonId?: string,
): BadgeLayout {
  const { nudge: nudgeMap } = prefsForCard(cardId, comparisonId)
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
  comparisonId?: string,
  mobile = false,
): BadgeLayout[] {
  const { side: sideMap } = prefsForCard(cardId, comparisonId, mobile)
  const preferred = sideMap?.[idx]
  const sides = preferred
    ? [preferred, ...defaultSideOrder(polygon).filter((side) => side !== preferred)]
    : defaultSideOrder(polygon)

  const seen = new Set<string>()
  const layouts: BadgeLayout[] = []
  for (const side of sides) {
    const layout = layoutOnSide(polygon, area, side, idx, cardId, comparisonId)
    const key = `${layout.badgeX.toFixed(1)}:${layout.badgeY.toFixed(1)}`
    if (seen.has(key)) continue
    seen.add(key)
    layouts.push(layout)
  }
  return layouts
}

function badgesOverlap(
  a: BadgeLayout,
  b: BadgeLayout,
  cardId?: string,
  comparisonId?: string,
  mobile = false,
): boolean {
  const { collisionRadius } = prefsForCard(cardId, comparisonId, mobile)
  const radius = collisionRadius ?? BADGE_COLLISION_RADIUS
  const dx = a.badgeX - b.badgeX
  const dy = a.badgeY - b.badgeY
  const minDist = radius * 2
  return dx * dx + dy * dy < minDist * minDist
}

function badgeInsideForeignPolygon(
  layout: BadgeLayout,
  ownIdx: number,
  regions: RegionForBadgeLayout[],
): boolean {
  return regions.some(
    (region) =>
      region.idx !== ownIdx &&
      pointInPolygon([layout.badgeX, layout.badgeY], region.polygonPct),
  )
}

function layoutValid(
  layout: BadgeLayout,
  ownIdx: number,
  ownPolygon: Point[],
  placed: BadgeLayout[],
  regions: RegionForBadgeLayout[],
  cardId?: string,
  comparisonId?: string,
  allowOnOwnRegion = false,
  mobile = false,
): boolean {
  if (!allowOnOwnRegion && pointInPolygon([layout.badgeX, layout.badgeY], ownPolygon)) return false
  if (placed.some((other) => badgesOverlap(layout, other, cardId, comparisonId, mobile))) return false
  if (badgeInsideForeignPolygon(layout, ownIdx, regions)) return false
  return true
}

function layoutScore(
  layout: BadgeLayout,
  idx: number,
  order: number,
  cardId?: string,
  comparisonId?: string,
  mobile = false,
): number {
  const { side: sideMap } = prefsForCard(cardId, comparisonId, mobile)
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

function nudgeLayout(
  layout: BadgeLayout,
  attempt: number,
  idx: number,
  cardId?: string,
  comparisonId?: string,
  mobile = false,
): BadgeLayout {
  const { side: sideMap } = prefsForCard(cardId, comparisonId, mobile)
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
  comparisonId?: string,
): BadgeLayout {
  const area = areaPct ?? polygonAreaAbs(polygonPct)
  const [cx, cy] = polygonCentroid(polygonPct)
  const bbox = polygonBBox(polygonPct)

  if (regionFitsBadgeInside(bbox, area) && !badgesAlwaysOutside(cardId, comparisonId)) {
    return { anchorX: cx, anchorY: cy, badgeX: cx, badgeY: cy, callout: false }
  }

  const candidates = candidateLayouts(polygonPct, area, idx ?? 0, cardId, comparisonId)
  return (
    candidates[0] ?? layoutOnSide(polygonPct, area, 'above', idx ?? 0, cardId, comparisonId)
  )
}

type RegionForBadgeLayout = {
  idx: number
  polygonPct: Point[]
  areaPct: number
  badgeLayout: BadgeLayout
}

/** Разводит кружки: не перекрывают друг друга и чужие подсветки. */
export function assignBadgeLayouts(
  regions: RegionForBadgeLayout[],
  cardId?: string,
  comparisonId?: string,
  options?: { mobile?: boolean },
): void {
  const mobile = options?.mobile ?? false
  const prefs = prefsForCard(cardId, comparisonId, mobile)
  const forceOnRegion = new Set(prefs.forceOnRegion ?? [])
  const placed: BadgeLayout[] = []
  const alwaysOutside = badgesAlwaysOutside(cardId, comparisonId)

  const placeRegion = (region: RegionForBadgeLayout) => {
    const bbox = polygonBBox(region.polygonPct)
    const onRegion = forceOnRegion.has(region.idx)

    if (onRegion) {
      const centered: BadgeLayout = {
        anchorX: region.badgeLayout.anchorX,
        anchorY: region.badgeLayout.anchorY,
        badgeX: region.badgeLayout.anchorX,
        badgeY: region.badgeLayout.anchorY,
        callout: false,
      }
      if (
        layoutValid(
          centered,
          region.idx,
          region.polygonPct,
          placed,
          regions,
          cardId,
          comparisonId,
          true,
          mobile,
        )
      ) {
        region.badgeLayout = centered
        placed.push(centered)
        return
      }
    }

    if (regionFitsBadgeInside(bbox, region.areaPct) && !alwaysOutside && !onRegion) {
      const centered: BadgeLayout = {
        anchorX: region.badgeLayout.anchorX,
        anchorY: region.badgeLayout.anchorY,
        badgeX: region.badgeLayout.anchorX,
        badgeY: region.badgeLayout.anchorY,
        callout: false,
      }
      if (
        layoutValid(
          centered,
          region.idx,
          region.polygonPct,
          placed,
          regions,
          cardId,
          comparisonId,
          false,
          mobile,
        )
      ) {
        region.badgeLayout = centered
        placed.push(centered)
        return
      }
    }

    const candidates = candidateLayouts(
      region.polygonPct,
      region.areaPct,
      region.idx,
      cardId,
      comparisonId,
      mobile,
    )
    let chosen: BadgeLayout | null = null
    let bestScore = Number.POSITIVE_INFINITY

    candidates.forEach((candidate, order) => {
      if (
        !layoutValid(
          candidate,
          region.idx,
          region.polygonPct,
          placed,
          regions,
          cardId,
          comparisonId,
          false,
          mobile,
        )
      ) {
        return
      }
      const score = layoutScore(candidate, region.idx, order, cardId, comparisonId, mobile)
      if (score < bestScore) {
        bestScore = score
        chosen = candidate
      }
    })

    if (!chosen) {
      const seed =
        candidates[0] ??
        computeBadgeLayout(region.polygonPct, region.areaPct, region.idx, cardId, comparisonId)
      chosen = seed
      for (let attempt = 0; attempt < 28; attempt += 1) {
        const nudged = nudgeLayout(seed, attempt, region.idx, cardId, comparisonId, mobile)
        if (
          layoutValid(
            nudged,
            region.idx,
            region.polygonPct,
            placed,
            regions,
            cardId,
            comparisonId,
            false,
            mobile,
          )
        ) {
          chosen = nudged
          break
        }
      }
    }

    region.badgeLayout = { ...chosen, callout: true }
    placed.push(chosen)
  }

  const forced = [...regions]
    .filter((region) => forceOnRegion.has(region.idx))
    .sort((a, b) => b.areaPct - a.areaPct)
  forced.forEach(placeRegion)

  const fixedSide = new Set(Object.keys(prefs.side ?? {}).map(Number))
  const pinned = [...regions]
    .filter((region) => !forceOnRegion.has(region.idx) && fixedSide.has(region.idx))
    .sort((a, b) => a.areaPct - b.areaPct)
  pinned.forEach(placeRegion)

  const rest = [...regions]
    .filter((region) => !forceOnRegion.has(region.idx) && !fixedSide.has(region.idx))
    .sort((a, b) => a.areaPct - b.areaPct)
  rest.forEach(placeRegion)
}

/** Мобильный фасад: все номера внизу кадра, выноски к центрам зон. */
export function assignMobileBottomBadgeLayouts(regions: RegionForBadgeLayout[]): void {
  const sorted = [...regions].sort((a, b) => a.idx - b.idx)
  const count = sorted.length
  if (count === 0) return

  const marginX = 7
  const bottomY = 92.5
  const span = 100 - marginX * 2

  sorted.forEach((region, index) => {
    const [cx, cy] = polygonCentroid(region.polygonPct)
    const badgeX = count === 1 ? 50 : marginX + (span * index) / (count - 1)
    region.badgeLayout = {
      anchorX: cx,
      anchorY: cy,
      badgeX: clampPct(badgeX),
      badgeY: bottomY,
      callout: true,
    }
  })
}
