import type { Confidence } from '../../types/building'

/** Цвет внутреннего кружка в квадратном маркере */
export const V2_CONFIDENCE_DOT: Record<Confidence, string> = {
  confirmed: '#059669',
  highly_probable: '#0284c7',
  probable: '#64748b',
  needs_verification: '#d97706',
  typological_hypothesis: '#1a4d3a',
}
