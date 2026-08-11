import { getConfidenceInfo } from '../../data/confidenceGuide'
import type { Confidence } from '../../types/building'
import { V2_CONFIDENCE_DOT } from '../lib/confidenceColors'
import { V2SquareMark } from './V2SquareMark'

export function V2ConfidenceBadge({
  level,
  title,
  showLabel = true,
}: {
  level: Confidence
  title?: string
  showLabel?: boolean
}) {
  const info = getConfidenceInfo(level)

  return (
    <span
      title={title ?? `${info.sourceTiers}. ${info.sourceExamples}`}
      className="inline-flex items-center gap-1.5"
    >
      <V2SquareMark innerColor={V2_CONFIDENCE_DOT[level]} size="sm" />
      {showLabel ? (
        <span className="v2-mono-xs v2-confidence-label text-v2-muted">{info.label}</span>
      ) : null}
    </span>
  )
}
