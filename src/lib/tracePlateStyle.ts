/** Единый стиль «стеклянных» карточек экспертных заметок (фасад + AR-симуляция). */
export const TRACE_PLATE_GLASS_BG = 'rgba(18, 53, 40, 0.75)'
export const TRACE_PLATE_HOVER_GLASS_BG = 'rgba(18, 53, 40, 0.65)'

export const TRACE_PLATE_SHELL_CLASS =
  'overflow-hidden rounded-2xl border border-arch-gold/60 text-left text-sm leading-relaxed text-arch-surface shadow-2xl backdrop-blur-xl'

export function tracePlateBackground(expanded: boolean): string {
  return expanded ? TRACE_PLATE_GLASS_BG : TRACE_PLATE_HOVER_GLASS_BG
}
