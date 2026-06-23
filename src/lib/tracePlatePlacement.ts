/** Позиция плашки у зоны: в верхней половине фасада — компактнее; развёрнутая карточка под якорем. */
export function tracePlatePlacement(
  cyPct: number,
  expanded: boolean,
): { transform: string; compact: boolean } {
  const compact = cyPct < 58
  const preferBelow = expanded && cyPct < 58
  return {
    compact,
    transform: preferBelow
      ? 'translate(-50%, 12px)'
      : 'translate(-50%, calc(-100% - 8px))',
  }
}
