import type { BuildingVerification, MemoryTrace } from '../types/building'
import { getConfidenceInfo } from '../data/confidenceGuide'
import { archiviewClassColor } from '../lib/archiviewClassColors'
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
  /** Класс зоны Archiview — цвет кружка как на фасаде и в списке */
  regionClass?: string
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
  regionClass,
  expanded,
  compact = false,
  onClose,
  className = '',
}: Props) {
  const badgeColor = archiviewClassColor(regionClass)
  const confidence = trace?.confidence
  const confidenceInfo = confidence ? getConfidenceInfo(confidence) : null
  const message = trace?.userMessage ?? comment ?? ''
  const { body, source: traceSource } = splitTraceMessage(message)
  const previewText = (comment?.trim() || body).trim()
  const confidenceBasis = confidence
    ? describeConfidenceBasis(confidence, traceSource, verification)
    : null
  const confidenceSourceLine = traceConfidenceSourceLine(traceSource, verification)
  const showSourceInConfidence = expanded && Boolean(confidenceInfo && confidenceSourceLine)

  return (
    <div className={className}>
      <div className="flex items-start gap-2.5">
        <span
          className={`mt-0.5 inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white ${
            expanded ? 'h-6 w-6 text-[13px]' : 'h-5 w-5 text-[11px]'
          }`}
          style={{ backgroundColor: badgeColor }}
        >
          {idx}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <span
              className={`block font-semibold leading-snug ${
                expanded ? 'text-[15px]' : 'line-clamp-2 text-[13px]'
              }`}
            >
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
                className="pointer-events-auto -mr-1 -mt-0.5 shrink-0 rounded-md px-1.5 py-0.5 text-xs font-semibold text-arch-surface/70 transition hover:bg-arch-surface/15 hover:text-arch-surface"
              >
                ✕
              </button>
            ) : null}
          </div>
          {period ? (
            <span
              className={`mt-0.5 block text-arch-surface/75 ${expanded ? 'text-[13px]' : 'text-[11px]'}`}
            >
              {period}
            </span>
          ) : null}

          {!expanded && previewText ? (
            <p className="mt-1.5 line-clamp-4 text-[12px] font-normal leading-snug text-arch-surface/85">
              {previewText}
            </p>
          ) : null}

          {expanded && body ? (
            <p
              className={`mt-2 text-[13px] font-normal leading-relaxed text-arch-surface/90 ${
                compact ? 'line-clamp-5' : ''
              }`}
            >
              {body}
            </p>
          ) : null}

          {expanded && confidenceInfo ? (
            <div className="mt-3.5 rounded-lg border border-arch-surface/20 bg-arch-surface/10 px-3 py-2.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-arch-surface/60">
                  Достоверность
                </span>
                <ConfidenceBadge level={confidenceInfo.value} />
              </div>
              <p className="mt-2 text-xs leading-relaxed text-arch-surface/80">{confidenceBasis}</p>
              {showSourceInConfidence ? (
                <p className="mt-1.5 text-xs leading-relaxed text-arch-surface/55">
                  Источник: {confidenceSourceLine}
                </p>
              ) : null}
            </div>
          ) : expanded && traceSource && !confidenceInfo ? (
            <p className="mt-2 text-xs leading-relaxed text-arch-surface/55">Источник: {traceSource}</p>
          ) : null}

          {expanded && !compact ? (
            <p className="mt-2.5 text-xs text-arch-surface/50">
              Повторный клик по зоне или заметке в списке — закрыть карточку
            </p>
          ) : null}
        </div>
      </div>
    </div>
  )
}
