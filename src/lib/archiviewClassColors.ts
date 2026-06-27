/** Цвета классов разметки Archiview — единые для подсветки, кружков и карточек артефактов. */
export const ARCHIVIEW_CLASS_COLORS: Record<string, string> = {
  added_floor: '#00aa00',
  extension: '#ff8c00',
  filled_window: '#0078d7',
  new_window: '#00aaaa',
  lost_balcony: '#b850b0',
  new_balcony: '#d08a00',
  changed_entrance: '#786cff',
  lost_decor: '#aa50ff',
  historical_signage: '#2896c8',
  lost_signage: '#c83c78',
  signage_rediscovered: '#ffc800',
  restored_signage: '#3cc83c',
  new_signage: '#ff8200',
  memorial_plaque: '#a07850',
  technical_artifact: '#7a8a00',
  other_artifact: '#8a8a00',
  check_manually: '#b000b0',
}

export function archiviewClassColor(cls?: string): string {
  if (!cls) return '#444444'
  return ARCHIVIEW_CLASS_COLORS[cls] ?? '#444444'
}
