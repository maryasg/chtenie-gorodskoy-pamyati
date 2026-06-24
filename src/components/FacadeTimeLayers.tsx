import { useEffect, useMemo, useState } from 'react'
import type { Building } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import {
  buildFacadeTimeLayerStack,
  fetchExplorerManifest,
  type FacadeTimeLayerStack,
  type FacadeTimeSnapshot,
} from '../data/explorer/explorerManifest'

type Props = {
  building: Building
  archiview: ArchiviewBuildingAssets
}

/** Прозрачность верхнего слоя: крайние годы — полностью, середина — полупрозрачно. */
function ghostOpacityForLayer(index: number, total: number): number {
  if (total <= 1) return 1
  if (index === 0 || index === total - 1) return 1
  const t = index / (total - 1)
  return Math.max(0.22, 0.92 - t * 0.55)
}

function layerHint(year: string, buildingId: string, label?: string): string {
  if (buildingId === 'MOSCOW_001_kumaninykh') {
    if (year === '1840') {
      return 'План усадьбы 1840 года — нижний слой шкалы; все снимки выровнены по этому холсту (4200×2452).'
    }
    if (year === '1924' && label?.includes('ГИМ')) {
      return 'Негатив Губарева А.А. (ГИМ, 9 марта 1924): двухэтажный усадебный облик, верхней надстройки ещё нет.'
    }
    if (year === '1924') {
      return 'Двухэтажное усадебное строение (1924): верхней надстройки ещё нет.'
    }
    if (year === '1930') {
      return 'Фасад в период строительства надстройки (около 1930 г.; на PastVu встречается подпись 1930–1936). По акту историко-культурной экспертизы (mos.ru, 2019) надстройку завершили в 1938 году — на снимке виден процесс, а не финальный облик.'
    }
    if (year === '2026') {
      return 'Современный фасад — полевая съёмка Archiview, 2026 год. Файл time-layers/2026.jpg выровнен по плану 1840.'
    }
  }
  if (buildingId === 'MOSCOW_002_turgenev_library') {
    if (year === '1934') {
      return 'Фасад до реконструкции под библиотеку (PastVu, 1934) — до раскрытия палат XVII–XVIII вв. при работах 1998–2003 (um.mos.ru).'
    }
  }
  if (year === '1840') return 'Ранний план или архивный срез — максимально далёкий от сегодняшнего облика.'
  return 'Промежуточный архивный снимок: часть деталей уже изменена или утрачена.'
}

/** Наложение срезов на план 1840 с полупрозрачным переходом. */
export function FacadeTimeLayers({ building, archiview }: Props) {
  const [stack, setStack] = useState<FacadeTimeLayerStack | null>(null)
  const [manifestLoaded, setManifestLoaded] = useState(false)
  const [layerIndex, setLayerIndex] = useState(0)
  const [ghostOverride, setGhostOverride] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    setManifestLoaded(false)

    if (!archiview.cardId) {
      setStack(null)
      setManifestLoaded(true)
      return
    }

    fetchExplorerManifest(archiview.cardId).then((manifest) => {
      if (cancelled) return
      const built = manifest ? buildFacadeTimeLayerStack(manifest, archiview.cardId) : null
      setStack(built)
      setLayerIndex(built ? built.layers.length - 1 : 0)
      setManifestLoaded(true)
    })

    return () => {
      cancelled = true
    }
  }, [archiview.cardId])

  const layers = stack?.layers ?? []
  const activeSnapshot: FacadeTimeSnapshot | null = layers[layerIndex] ?? null
  const isBaseLayer = layerIndex === 0
  const autoGhost = isBaseLayer ? 1 : ghostOpacityForLayer(layerIndex, layers.length)
  const ghostOpacity = ghostOverride ?? autoGhost

  const stageHint = useMemo(() => {
    if (!activeSnapshot) return ''
    return layerHint(activeSnapshot.year, building.id, activeSnapshot.label)
  }, [activeSnapshot, building.id])

  if (!manifestLoaded) {
    return (
      <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
        Загрузка слоёв времени…
      </p>
    )
  }

  if (!stack || layers.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
        Для слоёв времени нужны файлы в <code>time-layers/</code> (1840, 1924, 1930, 2026) — все
        4200×2452, выровнены по плану 1840.
      </p>
    )
  }

  const layerButtons = layers.map((snap) => ({
    key: `${snap.year}-${snap.label ?? ''}`,
    label: snap.label ?? snap.year,
  }))

  return (
    <div className="space-y-4">
      <p className="text-sm text-arch-muted">
        Нижний слой — план <strong>{stack.baseLabel}</strong>; поверх полупрозрачно накладывается
        выбранный год. Ползунок плавно показывает переход. Порядок:{' '}
        {layers.map((layer) => layer.label ?? layer.year).join(' → ')}.
      </p>

      <div className="overflow-hidden rounded-2xl border border-arch-line bg-arch-green-deep shadow-md">
        <div className="relative aspect-[4/3] max-h-[min(70vh,640px)] w-full bg-arch-green-deep">
          <img
            src={stack.baseUrl}
            alt={`Фасад ${stack.baseLabel}`}
            className="absolute inset-0 h-full w-full object-contain"
          />
          {activeSnapshot && !isBaseLayer ? (
            <img
              src={activeSnapshot.historicalUrl}
              alt={`Фасад ${activeSnapshot.label ?? activeSnapshot.year}`}
              className="pointer-events-none absolute inset-0 h-full w-full object-contain transition-opacity duration-300"
              style={{ opacity: ghostOpacity }}
            />
          ) : null}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/50 to-transparent" />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/55 to-transparent" />
          <div className="absolute left-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs text-white backdrop-blur-sm">
            {activeSnapshot?.label ?? activeSnapshot?.year ?? stack.baseLabel}
          </div>
          {!isBaseLayer ? (
            <div className="absolute bottom-3 right-3 rounded-md bg-black/55 px-2 py-1 text-xs tabular-nums text-white backdrop-blur-sm">
              слой {Math.round(ghostOpacity * 100)}%
            </div>
          ) : null}
        </div>
      </div>

      {!isBaseLayer && (
        <label className="block rounded-xl border border-arch-line bg-arch-surface px-3 py-2 text-sm">
          <span className="flex items-center justify-between text-arch-ink/80">
            <span>Прозрачность слоя {activeSnapshot?.label ?? activeSnapshot?.year}</span>
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
            Вернуть автоматически для выбранного года
          </button>
        </label>
      )}

      <section>
        <h3 className="mb-2 text-sm font-semibold text-arch-green-deep">Год на шкале</h3>
        <div className="flex flex-wrap gap-2">
          {layerButtons.map((btn, i) => (
            <button
              key={btn.key}
              type="button"
              onClick={() => {
                setLayerIndex(i)
                setGhostOverride(null)
              }}
              className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                i === layerIndex
                  ? 'border-arch-green-deep bg-arch-green-deep text-arch-surface shadow-sm'
                  : 'border-arch-line bg-arch-surface text-arch-muted hover:border-arch-green/40 hover:bg-arch-green-soft hover:text-arch-green-deep'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        <div className="mt-3 rounded-xl border border-arch-line bg-arch-surface p-4 shadow-sm">
          <p className="text-sm text-arch-ink/80">{stageHint}</p>
          {activeSnapshot?.sourceUrl ? (
            <p className="mt-2 text-xs text-arch-muted">
              Источник:{' '}
              <a
                href={activeSnapshot.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-arch-green underline"
              >
                каталог ГИМ
              </a>
            </p>
          ) : null}
        </div>
      </section>
    </div>
  )
}
