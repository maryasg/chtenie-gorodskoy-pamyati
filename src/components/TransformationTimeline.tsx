import type { TimelineStage } from '../types/building'
import { ConfidenceBadge } from './ConfidenceBadge'

export function TransformationTimeline({ stages }: { stages: TimelineStage[] }) {
  if (stages.length === 0) {
    return <p className="text-sm text-stone-500">Нет данных по этапам трансформации.</p>
  }

  return (
    <ol className="relative border-l-2 border-stone-300 pl-6">
      {stages.map((stage) => (
        <li key={stage.id} className="mb-6 last:mb-0">
          <span className="absolute -left-[9px] mt-1.5 h-4 w-4 rounded-full border-2 border-white bg-stone-400" />
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-stone-900">{stage.period}</span>
            <span className="text-stone-600">— {stage.title}</span>
            <ConfidenceBadge level={stage.confidence} />
          </div>
          <p className="mt-1 text-sm text-stone-700">
            <strong>Изменилось:</strong> {stage.whatChanged}
          </p>
          <p className="mt-1 text-sm text-stone-600">
            <strong>Видно сегодня:</strong> {stage.visibleToday}
          </p>
          {stage.source && (
            <p className="mt-1 text-xs text-stone-500">Источник: {stage.source}</p>
          )}
        </li>
      ))}
    </ol>
  )
}
