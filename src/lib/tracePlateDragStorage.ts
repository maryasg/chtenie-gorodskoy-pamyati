export type PlateDragPosition = { leftPct: number; topPct: number }

export type PlateDragMap = Record<number, PlateDragPosition>

const STORAGE_PREFIX = 'archiview-trace-plate-pos:'

export function loadPlateDragPositions(cardId: string): PlateDragMap {
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${cardId}`)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as PlateDragMap
    return parsed && typeof parsed === 'object' ? parsed : {}
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
