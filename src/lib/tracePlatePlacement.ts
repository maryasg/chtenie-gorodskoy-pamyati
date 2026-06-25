export type TracePlateSurface = 'sidebar' | 'facade'

export type TracePlatePlacement = {
  surface: TracePlateSurface
  leftPct: number
  topPct: number
  transform: string
  compact: boolean
}

/**
 * Позиция плашки: не перекрывать подсвеченную зону.
 * На десктопе с боковым списком — поверх списка справа; иначе смещение вниз/вбок от зоны.
 */
export function tracePlatePlacement(
  cxPct: number,
  cyPct: number,
  expanded: boolean,
  options?: { sidebarLayout?: boolean },
): TracePlatePlacement {
  const sidebarLayout = options?.sidebarLayout ?? false

  if (sidebarLayout) {
    return {
      surface: 'sidebar',
      leftPct: 0,
      topPct: 0,
      transform: '',
      compact: !expanded,
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
