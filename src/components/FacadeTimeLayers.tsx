import { useMemo, useState } from 'react'
import type { Building, TimelineStage } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import { ConfidenceBadge } from './ConfidenceBadge'

type Props = {
  building: Building
  archiview: ArchiviewBuildingAssets
}

/** Насколько «проявляется» исторический слой на каждом этапе шкалы */
const GHOST_BY_STAGE_INDEX = [0.88, 0.45, 0.12]

function stageGhostOpacity(index: number, total: number): number {
  if (total <= 1) return 0.85
  const preset = GHOST_BY_STAGE_INDEX[index]
  if (preset != null) return preset
  const t = index / (total - 1)
  return Math.max(0, 0.9 - t * 0.9)
}

/** Наложение исторического «призрака» на выпрямленную пару — для блока сравнения, не для AR. */
export function FacadeTimeLayers({ building, archiview }: Props) {
  const stages = building.timeline
  const [stageIndex, setStageIndex] = useState(stages.length > 0 ? stages.length - 1 : 0)
  const [ghostOverride, setGhostOverride] = useState<number | null>(null)

  const activeStage: TimelineStage | undefined = stages[stageIndex]
  const autoGhost = stageGhostOpacity(stageIndex, stages.length)
  const ghostOpacity = ghostOverride ?? autoGhost

  const modernUrl = archiview.modernRectifiedUrl
  const historicalUrl = archiview.historicalRectifiedUrl
  const hasPair = Boolean(modernUrl && historicalUrl)

  const stageHint = useMemo(() => {
    if (!activeStage) return ''
    if (stageIndex === 0) return 'Максимально близко к первоначальному облику по архивному фото.'
    if (stageIndex === stages.length - 1) return 'Современный фасад — то, что видно сегодня на месте.'
    return 'Промежуточный слой: часть исторических деталей уже утрачена или изменена.'
  }, [activeStage, stageIndex, stages.length])

  if (!hasPair) {
    return (
      <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
        Для слоёв времени нужна пара выпрямленных фото из Archiview. Экспортируйте{' '}
        <code>copy_to_website.bat</code> → Push.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-arch-muted">
        Выпрямленные снимки: современный фасад как основа, поверх — полупрозрачный исторический
        слой. Шкала этапов совпадает с блоком «Исторические слои» ниже на карточке.
      </p>

      <div className="overflow-hidden rounded-2xl border border-arch-line bg-arch-green-deep shadow-md">
        <div className="relative aspect-[4/3] max-h-[min(70vh,640px)] w-full bg-arch-green-deep">
          <img
            src={modernUrl}
            alt="Современный фасад"
            className="absolute inset-0 h-full w-full object-contain"
          />
          <img
            src={historicalUrl}
            alt="Исторический фасад"
            className="pointer-events-none absolute inset-0 h-full w-full object-contain transition-opacity duration-300"
            style={{ opacity: ghostOpacity }}
          />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/50 to-transparent" />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/55 to-transparent" />
          <div className="absolute left-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs text-white backdrop-blur-sm">
            {archiview.historicalPhotoYear ?? 'архив'} → {archiview.modernPhotoYear ?? 'сегодня'}
          </div>
          <div className="absolute bottom-3 right-3 rounded-md bg-black/55 px-2 py-1 text-xs tabular-nums text-white backdrop-blur-sm">
            призрак {Math.round(ghostOpacity * 100)}%
          </div>
        </div>
      </div>

      <label className="block rounded-xl border border-arch-line bg-arch-surface px-3 py-2 text-sm">
        <span className="flex items-center justify-between text-arch-ink/80">
          <span>Сила исторического слоя</span>
          <span className="font-medium tabular-nums">{Math.round(ghostOpacity * 100)}%</span>
        </span>
        <input
          type="range"
          min={0}
          max={100}
          value={Math.round(ghostOpacity * 100)}
          onChange={(e) => setGhostOverride(Number(e.target.value) / 100)}
          className="mt-2 w-full accent-arch-green"
        />
        <button
          type="button"
          onClick={() => setGhostOverride(null)}
          className="mt-1 text-xs text-arch-green underline"
        >
          Вернуть автоматически для выбранного этапа
        </button>
      </label>

      {stages.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-semibold text-arch-green-deep">Этап на шкале</h3>
          <div className="flex flex-wrap gap-2">
            {stages.map((stage, i) => (
              <button
                key={stage.id}
                type="button"
                onClick={() => {
                  setStageIndex(i)
                  setGhostOverride(null)
                }}
                className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                  i === stageIndex
                    ? 'border-arch-green-deep bg-arch-green-deep text-arch-surface shadow-sm'
                    : 'border-arch-line bg-arch-surface text-arch-muted hover:border-arch-green/40 hover:bg-arch-green-soft hover:text-arch-green-deep'
                }`}
              >
                {stage.period}
              </button>
            ))}
          </div>

          {activeStage && (
            <div className="mt-3 rounded-xl border border-arch-line bg-arch-surface p-4 shadow-sm">
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="font-semibold text-arch-green-deep">{activeStage.title}</h4>
                <ConfidenceBadge level={activeStage.confidence} />
                <span className="text-sm text-arch-muted">{activeStage.period}</span>
              </div>
              <p className="mt-2 text-sm text-arch-ink/80">{stageHint}</p>
              <p className="mt-2 text-sm text-arch-ink/80">
                <strong>Изменилось:</strong> {activeStage.whatChanged}
              </p>
              <p className="mt-1 text-sm text-arch-muted">
                <strong>Видно сегодня:</strong> {activeStage.visibleToday}
              </p>
              {activeStage.source && (
                <p className="mt-2 text-xs text-arch-muted">Источник: {activeStage.source}</p>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
