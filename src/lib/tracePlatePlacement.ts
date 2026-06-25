export type TracePlateSurface = 'sidebar' | 'facade'

/** Вертикальная зона плашки в правой колонке (MOSCOW_003). */
export type Moscow003PlateZone = 'orange' | 'red' | 'blue'

export type TracePlatePlacement = {
  surface: TracePlateSurface
  leftPct: number
  topPct: number
  transform: string
  compact: boolean
  /** % от высоты блока фасада — куда ставить плашку в правой колонке */
  sidebarTopPct?: number
}

/** Группы кружков → зона плашки справа (разметка Maria). */
const MOSCOW_003_PLATE_ZONE: Record<number, Moscow003PlateZone> = {
  // Оранжевая обводка — правая верхняя часть фасада
  3: 'orange',
  4: 'orange',
  5: 'orange',
  13: 'orange',
  14: 'orange',
  // Красная обводка — левая / верхняя часть
  6: 'red',
  7: 'red',
  8: 'red',
  9: 'red',
  12: 'red',
  // Синяя обводка — низ по центру
  1: 'blue',
  2: 'blue',
  10: 'blue',
  11: 'blue',
}

const MOSCOW_003_SIDEBAR_TOP: Record<Moscow003PlateZone, number> = {
  orange: 6,
  red: 30,
  blue: 58,
}

function moscow003SidebarTopPct(regionIdx: number): number {
  const zone = MOSCOW_003_PLATE_ZONE[regionIdx]
  return zone ? MOSCOW_003_SIDEBAR_TOP[zone] : MOSCOW_003_SIDEBAR_TOP.red
}

/**
 * Позиция плашки: не перекрывать подсвеченную зону.
 * MOSCOW_003 + боковой список: плашка в своей вертикальной зоне справа.
 */
export function tracePlatePlacement(
  cxPct: number,
  cyPct: number,
  expanded: boolean,
  options?: { sidebarLayout?: boolean; cardId?: string; regionIdx?: number },
): TracePlatePlacement {
  const sidebarLayout = options?.sidebarLayout ?? false
  const cardId = options?.cardId
  const regionIdx = options?.regionIdx

  if (sidebarLayout) {
    const sidebarTopPct =
      cardId === 'MOSCOW_003' && regionIdx != null
        ? moscow003SidebarTopPct(regionIdx)
        : 4

    return {
      surface: 'sidebar',
      leftPct: 0,
      topPct: 0,
      transform: '',
      compact: !expanded,
      sidebarTopPct,
    }
  }

  const leftPct = Math.min(86, Math.max(14, cxPct))

  if (expanded) {
    if (cyPct < 48) {
      return {
        surface: 'facade',
        leftPct,
        topPct: 92,
        transform: 'translate(-50%, -100%)',
        compact: false,
      }
    }
    if (cyPct > 58) {
      return {
        surface: 'facade',
        leftPct,
        topPct: 8,
        transform: 'translate(-50%, 0)',
        compact: false,
      }
    }
    const sidePct = cxPct < 50 ? 76 : 24
    return {
      surface: 'facade',
      leftPct: sidePct,
      topPct: cyPct,
      transform: 'translate(-50%, -50%)',
      compact: false,
    }
  }

  if (cyPct < 40) {
    return {
      surface: 'facade',
      leftPct,
      topPct: Math.min(94, cyPct + 16),
      transform: 'translate(-50%, 0)',
      compact: true,
    }
  }
  if (cyPct > 66) {
    return {
      surface: 'facade',
      leftPct,
      topPct: Math.max(6, cyPct - 16),
      transform: 'translate(-50%, -100%)',
      compact: true,
    }
  }

  const sidePct = cxPct < 50 ? 74 : 26
  return {
    surface: 'facade',
    leftPct: sidePct,
    topPct: cyPct,
    transform: 'translate(-50%, -50%)',
    compact: true,
  }
}
