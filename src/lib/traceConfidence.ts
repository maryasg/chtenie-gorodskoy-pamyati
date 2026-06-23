import type { BuildingVerification, Confidence } from '../types/building'
import { getConfidenceInfo } from '../data/confidenceGuide'

function formatExpertise(verification: BuildingVerification): string | undefined {
  const act = verification.officialExpertise?.[0]
  if (!act) return undefined
  return act.issuedAt ? `${act.title} (${act.issuedAt})` : act.title
}

/** Обоснование статуса достоверности по конкретным источникам заметки, не по методическим примерам. */
export function describeConfidenceBasis(
  confidence: Confidence,
  traceSource: string | undefined,
  verification?: BuildingVerification,
): string {
  const info = getConfidenceInfo(confidence)

  if (traceSource) {
    if (confidence === 'confirmed' && /акт|экспертиз|кгиоп|реестр|mos\.ru/i.test(traceSource)) {
      return `Статус «${info.label}» — зафиксирован официальный документ или реестр (см. источник).`
    }
    if (confidence === 'highly_probable') {
      return `Статус «${info.label}» — сильная аргументация по источникам; прямой строчки в акте по этой зоне нет.`
    }
    if (confidence === 'probable') {
      return `Статус «${info.label}» — вывод по сопоставлению снимков и полевой съёмки.`
    }
    if (confidence === 'needs_verification') {
      return `Статус «${info.label}» — пока опора на указанные источники; нужна дополнительная сверка.`
    }
    return `Статус «${info.label}» выбран с опорой на указанные источники.`
  }

  if (confidence === 'confirmed' && verification?.officialExpertise?.length) {
    const label = formatExpertise(verification)
    return label
      ? `Статус «${info.label}» — вывод по ${label}.`
      : info.hint
  }

  return info.hint
}

/** Конкретный источник для блока достоверности (не методические примеры). */
export function traceConfidenceSourceLine(
  traceSource: string | undefined,
  verification?: BuildingVerification,
): string | undefined {
  if (traceSource) return traceSource

  if (verification?.officialExpertise?.length) {
    return verification.officialExpertise
      .map((item) => (item.issuedAt ? `${item.title} (${item.issuedAt})` : item.title))
      .join('; ')
  }

  return undefined
}
