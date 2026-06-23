/** Позиция плашки у зоны: не вылезает за края окна сравнения. */
export function tracePlatePlacement(
  cxPct: number,
  cyPct: number,
  expanded: boolean,
): { transform: string; compact: boolean; leftPct: number; topPct: number } {
  const compact = !expanded
  const leftPct = Math.min(86, Math.max(14, cxPct))
  const topPct = cyPct

  const preferBelow = expanded ? cyPct < 58 : cyPct < 38
  const preferAbove = !expanded && cyPct > 68

  let transform: string
  if (preferBelow) {
    transform = 'translate(-50%, 12px)'
  } else if (preferAbove) {
    transform = 'translate(-50%, calc(-100% - 10px))'
  } else {
    transform = expanded
      ? 'translate(-50%, calc(-100% - 8px))'
      : 'translate(-50%, calc(-100% - 10px))'
  }

  return { transform, compact, leftPct, topPct }
}
