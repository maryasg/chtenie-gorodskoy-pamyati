import { useState } from 'react'
import type { Building } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import { FacadeBeforeAfterSlider } from './FacadeBeforeAfterSlider'
import { FacadeTimeLayers } from './FacadeTimeLayers'

type ComparisonMode = 'slider' | 'layers'

type Props = {
  building: Building
  assets: ArchiviewBuildingAssets
}

export function FacadePhotoComparison({ building, assets }: Props) {
  const [mode, setMode] = useState<ComparisonMode>('slider')

  return (
    <div className="space-y-4">
      <div
        className="flex flex-wrap gap-2 rounded-xl border border-arch-line bg-arch-surface p-1"
        role="tablist"
        aria-label="Режим сравнения фотоматериалов"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'slider'}
          onClick={() => setMode('slider')}
          className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
            mode === 'slider'
              ? 'bg-arch-green-deep text-arch-surface shadow-sm'
              : 'text-arch-muted hover:bg-arch-green-soft hover:text-arch-green-deep'
          }`}
        >
          Ползунок до/после
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'layers'}
          onClick={() => setMode('layers')}
          className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
            mode === 'layers'
              ? 'bg-arch-green-deep text-arch-surface shadow-sm'
              : 'text-arch-muted hover:bg-arch-green-soft hover:text-arch-green-deep'
          }`}
        >
          Слои времени
        </button>
      </div>

      {mode === 'slider' ? (
        <FacadeBeforeAfterSlider
          historicalUrl={assets.historicalRectifiedUrl}
          modernUrl={assets.modernRectifiedUrl}
          historicalYear={assets.historicalPhotoYear}
          modernYear={assets.modernPhotoYear}
        />
      ) : (
        <FacadeTimeLayers building={building} archiview={assets} />
      )}

      <p className="text-xs leading-relaxed text-arch-muted">
        Сейчас сравнивается основная пара выпрямленных снимков из Archiview. Позже здесь можно
        добавить переключатели между другими парами (другой ракурс, промежуточная дата) — когда
        появятся в manifest сравнений.
      </p>
    </div>
  )
}
