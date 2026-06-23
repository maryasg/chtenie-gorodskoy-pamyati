import { polygonAreaAbs, polygonCentroid, type Point } from './archiviewGeometry'

/** Площадь в %²: кружок можно класть на центр крупной зоны. */
const BADGE_ON_REGION_AREA = 110

/** Мелкая зона — выноска со стрелкой, чтобы не перекрывать подсветку. */
const CALLOUT_EXTRA_OFFSET = 2.2

export type BadgeLayout = {
  anchorX: number
  anchorY: number
  badgeX: number
  badgeY: number
  callout: boolean
}

function clampPct(value: number): number {
  return Math.min(98, Math.max(2, value))
}

/**
 * Крупная зона — номер на области; мелкая — выносной кружок со штрихом к якорю.
 */
export function computeBadgeLayout(polygonPct: Point[], areaPct?: number): BadgeLayout {
  const [cx, cy] = polygonCentroid(polygonPct)
  const area = areaPct ?? polygonAreaAbs(polygonPct)

  if (area >= BADGE_ON_REGION_AREA) {
    return { anchorX: cx, anchorY: cy, badgeX: cx, badgeY: cy, callout: false }
  }

  const compact = area < 90
  let offsetY = -(3.8 + (compact ? CALLOUT_EXTRA_OFFSET : 0))
  let offsetX = 0

  if (cx < 22) offsetX = 4
  else if (cx > 78) offsetX = -4
  else if (cx < 50) offsetX = -2.5
  else offsetX = 2.5

  if (cy < 18) {
    offsetY = 4.5
    offsetX *= 0.6
  }

  return {
    anchorX: cx,
    anchorY: cy,
    badgeX: clampPct(cx + offsetX),
    badgeY: clampPct(cy + offsetY),
    callout: true,
  }
}
