import type { MemoryTrace } from '../types/building'
import { getConfidenceInfo } from '../data/confidenceGuide'
import { ConfidenceBadge } from './ConfidenceBadge'
import { splitTraceMessage, TraceMessageBody } from '../lib/traceMessage'

type Props = {
  idx: number
  title: string
  period?: string
  trace?: MemoryTrace
  comment?: string
  /** Полная карточка (по клику) или краткий превью (при наведении) */
  expanded: boolean
  className?: string
}

export function CuratorTracePlate({
  idx,
  title,
  period,
  trace,
  comment,
  expanded,
  className = '',
}: Props) {
  const confidence = trace?.confidence
  const confidenceInfo = confidence ? getConfidenceInfo(confidence) : null
  const message = trace?.userMessage ?? comment ?? ''
  const hasListedSources = Boolean(splitTraceMessage(message).source)

  return (
    <div className={className}>
      <div className="flex items-start gap-2">
        <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-arch-gold text-[11px] font-bold text-arch-green-deep">
          {idx}
        </span>
        <div className="min-w-0 flex-1">
          <span className="block font-semibold leading-snug">{title}</span>
          {period ? (
            <span className="mt-0.5 block text-[11px] text-arch-surface/75">{period}</span>
          ) : null}

          {message ? (
            <div className="mt-1.5 text-[11px] font-normal leading-snug">
              {expanded ? (
                <TraceMessageBody
                  text={message}
                  bodyClassName="text-arch-surface/90"
                  sourceClassName="text-[10px] leading-snug text-arch-surface/55"
                />
              ) : (
                <TraceMessageBody
                  text={message.length > 220 ? `${message.slice(0, 220).trim()}…` : message}
                  bodyClassName="text-arch-surface/90"
                  sourceClassName="text-[10px] leading-snug text-arch-surface/55"
                />
              )}
            </div>
          ) : null}

          {expanded && confidenceInfo ? (
            <div className="mt-3 rounded-lg border border-arch-surface/20 bg-arch-surface/10 px-2.5 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-arch-surface/60">
                  Достоверность
                </span>
                <ConfidenceBadge level={confidenceInfo.value} />
              </div>
              <p className="mt-1.5 text-[10px] leading-snug text-arch-surface/80">
                {confidenceInfo.hint}
                {hasListedSources
                  ? ' Статус выбран с опорой на источники ниже.'
                  : ' Для этой зоны прямых источников в тексте пока нет — статус по методике.'}
              </p>
              <p className="mt-1 text-[10px] leading-snug text-arch-surface/55">
                Уровень источников: {confidenceInfo.sourceTiers}. Примеры:{' '}
                {confidenceInfo.sourceExamples}
              </p>
            </div>
          ) : null}

          {expanded ? (
            <p className="mt-2 text-[10px] text-arch-surface/50">
              Повторный клик по заметке — закрыть карточку
            </p>
          ) : null}
        </div>
      </div>
    </div>
  )
}
