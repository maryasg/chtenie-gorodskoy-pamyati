import type { Confidence } from '../types/building'

export type ConfidenceLevelInfo = {
  value: Confidence
  label: string
  /** Короткая подсказка для куратора и зрителя */
  hint: string
  /** Какие уровни источников подходят */
  sourceTiers: string
  /** Примеры источников */
  sourceExamples: string
  badgeClass: string
}

/** Порядок: от более надёжного к менее надёжному. */
export const CONFIDENCE_LEVELS: ConfidenceLevelInfo[] = [
  {
    value: 'confirmed',
    label: 'Подтверждено',
    hint: 'Факт зафиксирован официально или в авторитетном реестре.',
    sourceTiers: 'Высший + Высокий',
    sourceExamples:
      'Акт историко-культурной экспертизы (mos.ru), решения КГИОП, ГИМ, РГАЛИ, реестр «Узнай Москву»',
    badgeClass: 'bg-emerald-100 text-emerald-900 border-emerald-300',
  },
  {
    value: 'highly_probable',
    label: 'Высокая вероятность',
    hint: 'Сильная аргументация в научной литературе, но без прямой строчки в акте по этой зоне.',
    sourceTiers: 'Средний',
    sourceExamples: 'Научные статьи, диссертации, монографии по кварталу или типу застройки',
    badgeClass: 'bg-sky-100 text-sky-900 border-sky-300',
  },
  {
    value: 'probable',
    label: 'Вероятно',
    hint: 'Хорошо видно на сопоставлении снимков; датировку снимка желательно уточнить.',
    sourceTiers: 'Хороший',
    sourceExamples: 'PastVu, дореволюционные фото, планы (например 1840 г.), полевая съёмка + Archiview',
    badgeClass: 'bg-slate-100 text-slate-800 border-slate-300',
  },
  {
    value: 'needs_verification',
    label: 'Требует проверки',
    hint: 'Пока опора на слабые или вторичные источники — нужна сверка куратором.',
    sourceTiers: 'Ниже + Осторожно',
    sourceExamples: 'Статьи СМИ, блоги, форумы, Wikipedia без ссылки на первоисточник',
    badgeClass: 'bg-amber-100 text-amber-900 border-amber-300',
  },
  {
    value: 'typological_hypothesis',
    label: 'Типологическая гипотеза',
    hint: 'Вывод по аналогии с другими зданиями; для этого объекта прямого источника нет.',
    sourceTiers: 'Нет прямого источника',
    sourceExamples: 'Сравнение с типовыми приёмами эпохи, пока не подтверждено документом или снимком',
    badgeClass: 'bg-arch-green-soft text-arch-green-deep border-arch-green/30',
  },
]

const BY_VALUE = new Map(CONFIDENCE_LEVELS.map((item) => [item.value, item]))

export function getConfidenceInfo(level: Confidence): ConfidenceLevelInfo {
  return BY_VALUE.get(level) ?? BY_VALUE.get('needs_verification')!
}

export const CONFIDENCE_SELECT_OPTIONS = CONFIDENCE_LEVELS.map((item) => ({
  value: item.value,
  label: item.label,
  hint: `${item.sourceTiers}: ${item.sourceExamples}`,
}))
