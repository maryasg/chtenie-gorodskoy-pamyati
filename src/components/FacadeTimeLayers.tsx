import { useEffect, useMemo, useState } from 'react'
import type { Building } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import {
  buildFacadeTimeSnapshots,
  fetchExplorerManifest,
  type FacadeTimeSnapshot,
} from '../data/explorer/explorerManifest'

type Props = {
  building: Building
  archiview: ArchiviewBuildingAssets
}

/** Насколько «проявляется» исторический слой: чем раньше снимок, тем сильнее призрак. */
function ghostOpacityForSnapshot(index: number, total: number): number {
  if (total <= 0) return 0.85
  if (total === 1) return 0.85
  const t = index / (total - 1)
  return Math.max(0.12, 0.9 - t * 0.78)
}

function layerHint(year: string, buildingId: string, label?: string): string {
  if (buildingId === 'MOSCOW_001_kumaninykh') {
    if (year === '1840') {
      return 'План усадьбы 1840 года — исходная планировка проёмов и входов до поздних переделок.'
    }
    if (year === '1924' && label?.includes('ГИМ')) {
      return 'Негатив Губарева А.А. (ГИМ, 9 марта 1924): вид на Большую Ордынку; в каталоге — «дом № 15 (бывш. Жучковых)». Снимок не выпрямлялся в Archiview — показан как архивный кадр, не как наложение на современный фасад.'
    }
    if (year === '1924') {
      return 'Двухэтажное усадебное строение (PastVu, 1924): верхней надстройки ещё нет; в начале 1920-х рядом действовал Ордынский лагерь.'
    }
    if (year === '1938') {
      return 'Выпрямленный исторический снимок из основного сравнения Archiview (11 зон, cmp_005): тот же кадр, что и для интерактивной разметки фасада. Год надстройки по акту экспертизы — 1938.'
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

/** Наложение исторических «призраков» на современный выпрямленный фасад. */
export function FacadeTimeLayers({ building, archiview }: Props) {
  const [snapshots, setSnapshots] = useState<FacadeTimeSnapshot[]>([])
  const [manifestLoaded, setManifestLoaded] = useState(false)
  const [layerIndex, setLayerIndex] = useState(0)
  const [ghostOverride, setGhostOverride] = useState<number | null>(null)

  const modernUrl = archiview.modernRectifiedUrl
  const modernYear = archiview.modernPhotoYear ?? 'сегодня'
  const hasModern = Boolean(modernUrl)

  useEffect(() => {
    let cancelled = false
    setManifestLoaded(false)

    if (!archiview.cardId) {
      setSnapshots([])
      setManifestLoaded(true)
      return
    }

    fetchExplorerManifest(archiview.cardId).then((manifest) => {
      if (cancelled) return
      if (manifest?.comparisons?.length) {
        const built = buildFacadeTimeSnapshots(manifest, archiview.cardId)
        setSnapshots(built)
        setLayerIndex(built.length)
      } else if (archiview.historicalRectifiedUrl && archiview.historicalPhotoYear) {
        setSnapshots([
          {
            year: archiview.historicalPhotoYear,
            historicalUrl: archiview.historicalRectifiedUrl,
            comparisonId: 'default',
            comparisonTitle: `${archiview.historicalPhotoYear} → ${modernYear}`,
          },
        ])
        setLayerIndex(1)
      } else {
        setSnapshots([])
      }
      setManifestLoaded(true)
    })

    return () => {
      cancelled = true
    }
  }, [
    archiview.cardId,
    archiview.historicalPhotoYear,
    archiview.historicalRectifiedUrl,
    modernYear,
  ])

  const isModernLayer = layerIndex >= snapshots.length
  const activeSnapshot = isModernLayer ? null : snapshots[layerIndex]
  const autoGhost = isModernLayer ? 0 : ghostOpacityForSnapshot(layerIndex, snapshots.length)
  const ghostOpacity = ghostOverride ?? autoGhost

  const stageHint = useMemo(() => {
    if (isModernLayer) return 'Современный фасад — то, что видно сегодня на месте (полевая съёмка).'
    if (!activeSnapshot) return ''
    return layerHint(activeSnapshot.year, building.id, activeSnapshot.label)
  }, [activeSnapshot, building.id, isModernLayer])

  const isArchiveLayer = !isModernLayer && activeSnapshot?.overlayMode === 'archive'

  if (!manifestLoaded) {
    return (
      <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
        Загрузка слоёв времени…
      </p>
    )
  }

  if (!hasModern || snapshots.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
        Для слоёв времени нужны выпрямленные снимки из Archiview (1840, 1924, 1938 и современный).
        Экспортируйте <code>copy_to_website.bat</code> → Push.
      </p>
    )
  }

  const layerButtons = [
    ...snapshots.map((snap) => ({ key: `${snap.year}-${snap.label ?? ''}`, label: snap.label ?? snap.year })),
    { key: 'modern', label: modernYear },
  ]

  return (
    <div className="space-y-4">
      <p className="text-sm text-arch-muted">
        Современный фасад ({modernYear}) — основа; поверх полупрозрачный исторический слой выбранного
        года. Порядок: {snapshots.map((s) => s.year).join(' → ')} → {modernYear}.
      </p>

      <div className="overflow-hidden rounded-2xl border border-arch-line bg-arch-green-deep shadow-md">
        <div className="relative aspect-[4/3] max-h-[min(70vh,640px)] w-full bg-arch-green-deep">
          {isArchiveLayer ? (
            <>
              <img
                src={activeSnapshot!.historicalUrl}
                alt={`Архивный снимок ${activeSnapshot!.label ?? activeSnapshot!.year}`}
                className="absolute inset-0 h-full w-full object-contain"
              />
              <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/50 to-transparent" />
              <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/55 to-transparent" />
              <div className="absolute left-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs text-white backdrop-blur-sm">
                {activeSnapshot!.label ?? activeSnapshot!.year}
              </div>
            </>
          ) : (
            <>
              <img
                src={modernUrl}
                alt="Современный фасад"
                className="absolute inset-0 h-full w-full object-contain"
              />
              {activeSnapshot ? (
                <img
                  src={activeSnapshot.historicalUrl}
                  alt={`Фасад ${activeSnapshot.year} года`}
                  className="pointer-events-none absolute inset-0 h-full w-full object-contain transition-opacity duration-300"
                  style={{ opacity: ghostOpacity }}
                />
              ) : null}
              <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/50 to-transparent" />
              <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/55 to-transparent" />
              <div className="absolute left-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs text-white backdrop-blur-sm">
                {isModernLayer
                  ? modernYear
                  : `${activeSnapshot!.year} → ${modernYear}`}
              </div>
              {!isModernLayer ? (
                <div className="absolute bottom-3 right-3 rounded-md bg-black/55 px-2 py-1 text-xs tabular-nums text-white backdrop-blur-sm">
                  призрак {Math.round(ghostOpacity * 100)}%
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>

      {!isModernLayer && !isArchiveLayer && (
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
          {!isModernLayer && activeSnapshot ? (
            <>
              {activeSnapshot.sourceUrl ? (
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
              ) : (
                <p className="mt-2 text-xs text-arch-muted">
                  Сравнение Archiview: {activeSnapshot.comparisonTitle}
                </p>
              )}
            </>
          ) : null}
        </div>
      </section>
    </div>
  )
}
