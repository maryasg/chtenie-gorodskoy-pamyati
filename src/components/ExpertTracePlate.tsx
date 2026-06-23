import type { BuildingVerification, MemoryTrace } from '../types/building'
import { getConfidenceInfo } from '../data/confidenceGuide'
import { describeConfidenceBasis, traceConfidenceSourceLine } from '../lib/traceConfidence'
import { ConfidenceBadge } from './ConfidenceBadge'
import { splitTraceMessage } from '../lib/traceMessage'

type Props = {
  idx: number
  title: string
  period?: string
  trace?: MemoryTrace
  comment?: string
  verification?: BuildingVerification
  /** Полная карточка (по клику) или краткий превью (при наведении) */
  expanded: boolean
  /** Компактная карточка (верхние зоны фасада — не заезжает под меню) */
  compact?: boolean
  onClose?: () => void
  className?: string
}

export function ExpertTracePlate({
  idx,
  title,
  period,
  trace,
  comment,
  verification,
  expanded,
  compact = false,
  onClose,
  className = '',
}: Props) {
  const confidence = trace?.confidence
  const confidenceInfo = confidence ? getConfidenceInfo(confidence) : null
  const message = trace?.userMessage ?? comment ?? ''
  const { body, source: traceSource } = splitTraceMessage(message)
  const confidenceBasis = confidence
    ? describeConfidenceBasis(confidence, traceSource, verification)
    : null
  const confidenceSourceLine = traceConfidenceSourceLine(traceSource, verification)
  const showSourceInConfidence = expanded && Boolean(confidenceInfo && confidenceSourceLine)

  return (
    <div className={className}>
      <div className="flex items-start gap-2">
        <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-arch-gold text-[11px] font-bold text-arch-green-deep">
          {idx}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <span className={`block font-semibold leading-snug ${expanded ? '' : 'line-clamp-2'}`}>
              {title}
            </span>
            {expanded && onClose ? (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation()
                  onClose()
                }}
                aria-label="Закрыть карточку"
                className="pointer-events-auto -mr-1 -mt-0.5 shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-semibold text-arch-surface/70 transition hover:bg-arch-surface/15 hover:text-arch-surface"
              >
                ✕
              </button>
            ) : null}
          </div>
          {period ? (
            <span className="mt-0.5 block text-[11px] text-arch-surface/75">{period}</span>
          ) : null}

          {expanded && body ? (
            <p className="mt-1.5 text-[11px] font-normal leading-snug text-arch-surface/90">
              {body}
            </p>
          ) : null}

          {expanded && confidenceInfo ? (
            <div className="mt-3 rounded-lg border border-arch-surface/20 bg-arch-surface/10 px-2.5 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-arch-surface/60">
                  Достоверность
                </span>
                <ConfidenceBadge level={confidenceInfo.value} />
              </div>
              <p className="mt-1.5 text-[10px] leading-snug text-arch-surface/80">{confidenceBasis}</p>
              {showSourceInConfidence ? (
                <p className="mt-1 text-[10px] leading-snug text-arch-surface/55">
                  Источник: {confidenceSourceLine}
                </p>
              ) : null}
            </div>
          ) : expanded && traceSource && !confidenceInfo ? (
            <p className="mt-2 text-[10px] leading-snug text-arch-surface/55">Источник: {traceSource}</p>
          ) : null}

          {expanded && !compact ? (
            <p className="mt-2 text-[10px] text-arch-surface/50">
              Повторный клик по зоне или заметке в списке — закрыть карточку
            </p>
          ) : null}
        </div>
      </div>
    </div>
  )
}
