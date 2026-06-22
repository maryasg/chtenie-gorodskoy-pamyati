import type { Confidence } from '../types/building'
import { CONFIDENCE_LEVELS, getConfidenceInfo } from '../data/confidenceGuide'

export function ConfidenceBadge({
  level,
  title,
}: {
  level: Confidence
  /** Подсказка при наведении — уровень источников */
  title?: string
}) {
  const info = getConfidenceInfo(level)
  return (
    <span
      title={title ?? `${info.sourceTiers}. ${info.sourceExamples}`}
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${info.badgeClass}`}
    >
      {info.label}
    </span>
  )
}

export function ConfidenceLegend({ compact = false }: { compact?: boolean }) {
  return (
    <div className="space-y-3">
      {CONFIDENCE_LEVELS.map((item) => (
        <div
          key={item.value}
          className={
            compact
              ? 'flex flex-wrap items-start gap-2'
              : 'rounded-xl border border-arch-line bg-arch-surface-2/40 p-4'
          }
        >
          <ConfidenceBadge level={item.value} title={item.hint} />
          <div className="min-w-0 flex-1 text-sm">
            <p className="font-medium text-arch-ink">
              Уровень источников: <span className="text-arch-green-deep">{item.sourceTiers}</span>
            </p>
            <p className="mt-1 leading-relaxed text-arch-ink/80">{item.hint}</p>
            {!compact && (
              <p className="mt-2 text-xs leading-relaxed text-arch-muted">
                Примеры: {item.sourceExamples}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
