import { useMemo, useState } from 'react'
import type { Building, TimelineStage } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import { ConfidenceBadge } from './ConfidenceBadge'

type Props = {
  building: Building
  archiview?: ArchiviewBuildingAssets
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

export function FacadeARPreview({ building, archiview }: Props) {
  const stages = building.timeline
  const [stageIndex, setStageIndex] = useState(stages.length > 0 ? stages.length - 1 : 0)
  const [ghostOverride, setGhostOverride] = useState<number | null>(null)

  const activeStage: TimelineStage | undefined = stages[stageIndex]
  const autoGhost = stageGhostOpacity(stageIndex, stages.length)
  const ghostOpacity = ghostOverride ?? autoGhost

  const modernUrl = archiview?.modernRectifiedUrl
  const historicalUrl = archiview?.historicalRectifiedUrl
  const hasPair = Boolean(modernUrl && historicalUrl)

  const stageHint = useMemo(() => {
    if (!activeStage) return ''
    if (stageIndex === 0) return 'Максимально близко к первоначальному облику по архивному фото.'
    if (stageIndex === stages.length - 1) return 'Современный фасад — то, что видно сегодня на месте.'
    return 'Промежуточный слой: часть исторических деталей уже утрачена или изменена.'
  }, [activeStage, stageIndex, stages.length])

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-violet-200 bg-violet-50/70 p-4 text-sm text-violet-950">
        <strong>AR-preview (без камеры).</strong> Современный фасад как «окно на месте», поверх —
        призрак истории. Выберите этап на шкале — подсказки совпадают с блоком «Этапы трансформации»
        на карточке здания.
      </div>

      <div className="overflow-hidden rounded-2xl border border-stone-300 bg-stone-950 shadow-lg">
        <div className="flex items-center justify-between border-b border-stone-700/80 bg-stone-900 px-4 py-2 text-xs text-stone-400">
          <span>Режим: слои времени</span>
          {archiview?.modernPhotoYear && (
            <span className="tabular-nums">сегодня · {archiview.modernPhotoYear}</span>
          )}
        </div>

        <div className="relative aspect-[4/3] max-h-[min(70vh,640px)] w-full bg-stone-900">
          {hasPair ? (
            <>
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
                {archiview?.historicalPhotoYear ?? 'архив'} → {archiview?.modernPhotoYear ?? 'сегодня'}
              </div>
              <div className="absolute bottom-3 right-3 rounded-md bg-black/55 px-2 py-1 text-xs tabular-nums text-white backdrop-blur-sm">
                призрак {Math.round(ghostOpacity * 100)}%
              </div>
            </>
          ) : (
            <div className="flex h-full min-h-[240px] items-center justify-center p-6 text-center text-sm text-stone-400">
              Для этого здания ещё нет пары выпрямленных фото из Archiview. На карточке доступна схема
              hotspots.
            </div>
          )}

          <div className="pointer-events-none absolute inset-4 rounded-lg border border-white/20" aria-hidden />
        </div>
      </div>

      {hasPair && (
        <label className="block rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm">
          <span className="flex items-center justify-between text-stone-700">
            <span>Сила исторического слоя</span>
            <span className="font-medium tabular-nums">{Math.round(ghostOpacity * 100)}%</span>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round(ghostOpacity * 100)}
            onChange={(e) => setGhostOverride(Number(e.target.value) / 100)}
            className="mt-2 w-full accent-violet-600"
          />
          <button
            type="button"
            onClick={() => setGhostOverride(null)}
            className="mt-1 text-xs text-violet-700 underline"
          >
            Вернуть автоматически для выбранного этапа
          </button>
        </label>
      )}

      {stages.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Шкала времени</h2>
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
                    ? 'border-violet-600 bg-violet-600 text-white shadow-sm'
                    : 'border-stone-300 bg-white text-stone-700 hover:border-violet-300'
                }`}
              >
                {stage.period}
              </button>
            ))}
          </div>

          {activeStage && (
            <div className="mt-4 rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-semibold text-stone-900">{activeStage.title}</h3>
                <ConfidenceBadge level={activeStage.confidence} />
                <span className="text-sm text-stone-500">{activeStage.period}</span>
              </div>
              <p className="mt-2 text-sm text-stone-700">{stageHint}</p>
              <p className="mt-2 text-sm text-stone-700">
                <strong>Изменилось:</strong> {activeStage.whatChanged}
              </p>
              <p className="mt-1 text-sm text-stone-600">
                <strong>Видно сегодня:</strong> {activeStage.visibleToday}
              </p>
              {activeStage.source && (
                <p className="mt-2 text-xs text-stone-500">Источник: {activeStage.source}</p>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
