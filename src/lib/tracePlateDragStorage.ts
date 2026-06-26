/** Позиция центра плашки в % ширины/высоты окна браузера */
export type PlateDragPosition = { xPct: number; yPct: number }

export type PlateDragMap = Record<number, PlateDragPosition>

const STORAGE_PREFIX = 'archiview-trace-plate-vp:'

export function loadPlateDragPositions(cardId: string): PlateDragMap {
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${cardId}`)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as PlateDragMap
    if (!parsed || typeof parsed !== 'object') return {}
    const out: PlateDragMap = {}
    for (const [key, value] of Object.entries(parsed)) {
      const idx = Number(key)
      if (!Number.isFinite(idx) || !value || typeof value !== 'object') continue
      const v = value as Partial<PlateDragPosition>
      if (typeof v.xPct === 'number' && typeof v.yPct === 'number') {
        out[idx] = { xPct: v.xPct, yPct: v.yPct }
      }
    }
    return out
  } catch {
    return {}
  }
}

export function savePlateDragPositions(cardId: string, positions: PlateDragMap): void {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${cardId}`, JSON.stringify(positions))
  } catch {
    // localStorage недоступен — позиции только в сессии
  }
}

/** Автопозиция из координат блока фасада → центр плашки в % окна */
export function blockPctToViewportPct(
  leftPct: number,
  topPct: number,
  blockRect: DOMRect,
): PlateDragPosition {
  const x = blockRect.left + (blockRect.width * leftPct) / 100
  const y = blockRect.top + (blockRect.height * topPct) / 100
  return {
    xPct: (x / window.innerWidth) * 100,
    yPct: (y / window.innerHeight) * 100,
  }
}
