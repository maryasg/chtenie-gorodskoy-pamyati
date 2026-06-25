import { useEffect, useMemo, useRef, useState } from 'react'
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

type CrossfadeFrame = {
  from: FacadeTimeSnapshot
  to: FacadeTimeSnapshot
  /** 0 = только from, 1 = только to */
  blend: number
}

function crossfadeAtPosition(layers: FacadeTimeSnapshot[], positionPct: number): CrossfadeFrame {
  if (layers.length === 0) {
    throw new Error('crossfadeAtPosition: empty layers')
  }
  if (layers.length === 1) {
    return { from: layers[0], to: layers[0], blend: 0 }
  }

  const t = Math.max(0, Math.min(100, positionPct)) / 100
  const scaled = t * (layers.length - 1)
  const fromIndex = Math.floor(scaled)
  const toIndex = Math.min(fromIndex + 1, layers.length - 1)
  const blend = scaled - fromIndex

  return {
    from: layers[fromIndex],
    to: layers[toIndex],
    blend: fromIndex === toIndex ? 0 : blend,
  }
}

function sourceLinkLabel(url: string): string {
  if (url.includes('catalog.shm.ru') || url.includes('shm.ru')) return 'каталог ГИМ'
  if (url.includes('pastvu.com')) return 'PastVu (источник: Архив ЦИГИ)'
  if (url.includes('goskatalog.ru')) return 'Госкаталог'
  return 'источник'
}

function displayYearLabel(frame: CrossfadeFrame): string {
  if (frame.blend < 0.08 || frame.from.year === frame.to.year) {
    return frame.from.label ?? frame.from.year
  }
  if (frame.blend > 0.92) {
    return frame.to.label ?? frame.to.year
  }
  return `${frame.from.label ?? frame.from.year} → ${frame.to.label ?? frame.to.year}`
}

function emptyTimeLayersMessage(cardId?: string): string {
  if (cardId === 'MOSCOW_001') {
    return 'Для слоёв времени нужны файлы в time-layers/ (1840, 1924, 1930–1936, 2026) — все 4200×2452, выровнены по одному холсту.'
  }
  if (cardId === 'MOSCOW_003') {
    return 'Для слоёв времени нужны файлы в time-layers/ (1911, 2026 и др.) — все 4200×2452, выровнены по одному холсту.'
  }
  return 'Для слоёв времени нужен manifest.json с разделом timeLayers и файлы в time-layers/ — все 4200×2452, выровнены по одному холсту.'
}

function layerHint(year: string, buildingId: string, label?: string): string {
  if (buildingId === 'MOSCOW_001_kumaninykh') {
    if (year === '1840') {
      return 'План усадьбы 1840 года — все снимки выровнены по этому холсту (4200×2452).'
    }
    if (year === '1924' && label?.includes('ГИМ')) {
      return 'Негатив Губарева А.А. (ГИМ, 9 марта 1924): двухэтажный усадебный облик, верхней надстройки ещё нет.'
    }
    if (year === '1924') {
      return 'Двухэтажное усадебное строение (1924): верхней надстройки ещё нет.'
    }
    if (year === '1930') {
      return 'Строительство надстройки (1930–1936): снимок из Архива ЦИГИ (PastVu p/68053) — дом в лесах, три верхних яруса без отделки. По сравнению с другим архивным кадром 1934 г. (Госкаталог) и акту экспертизы снимок, вероятно, сделан около 1930 г. или чуть позже — до 1934. По акту историко-культурной экспертизы (mos.ru, 2019) надстройку завершили в 1938 году — на шкале этот слой фиксирует процесс, а не финальный облик.'
    }
    if (year === '2026') {
      return 'Современный фасад — полевая съёмка Archiview, 2026 год.'
    }
  }
  if (buildingId === 'MOSCOW_002_turgenev_library') {
    if (year === '1934') {
      return 'Фасад до реконструкции под библиотеку (PastVu, 1934) — до раскрытия палат XVII–XVIII вв. при работах 1998–2003 (um.mos.ru).'
    }
  }
  if (buildingId === 'MOSCOW_003_dom_so_zveryami') {
    if (year === '1911') {
      return 'Фото ~1911 г. (PastVu): доходный дом Л. Кравецкого до советской надстройки 1945 г. — шатровая башня, балконы, декор северного модерна. Слой-заглушка до финального выравнивания на холсте 4200×2452.'
    }
    if (year === '2026') {
      return 'Современный фасад — полевая съёмка Archiview, 2026 год. Слой-заглушка до финального выравнивания на холсте 4200×2452.'
    }
  }
  if (year === '1840') return 'Ранний план или архивный срез — максимально далёкий от сегодняшнего облика.'
  return 'Промежуточный архивный снимок: часть деталей уже изменена или утрачена.'
}

/** Длительность полного прохода шкалы 0→100 при автопроигрывании. */
const AUTOPLAY_MS_PER_LAYER = 4000

/** Шкала лет: плавный переход между снимками через затемнение (crossfade). */
export function FacadeTimeLayers({ building, archiview }: Props) {
  const [stack, setStack] = useState<FacadeTimeLayerStack | null>(null)
  const [manifestLoaded, setManifestLoaded] = useState(false)
  const [positionPct, setPositionPct] = useState(100)
  const [isPlaying, setIsPlaying] = useState(false)
  const positionRef = useRef(positionPct)
  const rafRef = useRef<number>(0)

  positionRef.current = positionPct

  const stopAutoplay = () => setIsPlaying(false)

  const setPositionManual = (pct: number) => {
    stopAutoplay()
    setPositionPct(pct)
  }

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
      setPositionPct(100)
      setIsPlaying(false)
      setManifestLoaded(true)
    })

    return () => {
      cancelled = true
    }
  }, [archiview.cardId])

  const layers = stack?.layers ?? []

  useEffect(() => {
    if (!isPlaying || layers.length < 2) return

    const durationMs = Math.max(8000, layers.length * AUTOPLAY_MS_PER_LAYER)
    let anchorTime = performance.now()
    let anchorPct = positionRef.current

    const step = (now: number) => {
      let pct = anchorPct + ((now - anchorTime) / durationMs) * 100
      if (pct >= 100) {
        anchorPct = 0
        anchorTime = now
        pct = 0
      }
      setPositionPct(pct)
      rafRef.current = requestAnimationFrame(step)
    }

    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
  }, [isPlaying, layers.length])

  const frame = layers.length ? crossfadeAtPosition(layers, positionPct) : null

  const stageHint = useMemo(() => {
    if (!frame) return ''
    const year = frame.blend >= 0.5 ? frame.to.year : frame.from.year
    const label = frame.blend >= 0.5 ? frame.to.label : frame.from.label
    return layerHint(year, building.id, label)
  }, [frame, building.id])

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
        {emptyTimeLayersMessage(archiview.cardId)}
      </p>
    )
  }

  const firstYear = layers[0].label ?? layers[0].year
  const lastYear = layers[layers.length - 1].label ?? layers[layers.length - 1].year
  const fromOpacity = frame ? 1 - frame.blend : 1
  const toOpacity = frame ? frame.blend : 0

  return (
    <div className="space-y-4">
      <p className="text-sm text-arch-muted">
        Двигайте ползунок по годам — снимки сменяют друг друга через плавное затемнение. Можно
        запустить автопроигрывание под шкалой. Порядок:{' '}
        {layers.map((layer) => layer.label ?? layer.year).join(' → ')}.
      </p>

      <div className="overflow-hidden rounded-2xl border border-arch-line bg-arch-green-deep shadow-md">
        <div className="relative aspect-[4/3] max-h-[min(70vh,640px)] w-full bg-arch-green-deep">
          {frame ? (
            <>
              <img
                src={frame.from.historicalUrl}
                alt={`Фасад ${frame.from.label ?? frame.from.year}`}
                className="absolute inset-0 h-full w-full object-contain transition-opacity duration-200"
                style={{ opacity: fromOpacity }}
              />
              <img
                src={frame.to.historicalUrl}
                alt={`Фасад ${frame.to.label ?? frame.to.year}`}
                className="pointer-events-none absolute inset-0 h-full w-full object-contain transition-opacity duration-200"
                style={{ opacity: toOpacity }}
              />
            </>
          ) : null}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/50 to-transparent" />
          <div className="absolute left-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs text-white backdrop-blur-sm">
            {frame ? displayYearLabel(frame) : ''}
          </div>
        </div>

        <div className="border-t border-arch-line/40 bg-arch-surface px-3 py-3 text-sm">
          <span className="mb-2 flex items-center justify-between text-arch-ink/80">
            <span>Год на шкале</span>
            <span className="font-semibold tabular-nums text-arch-green-deep">
              {frame ? displayYearLabel(frame) : ''}
            </span>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={0.5}
            value={positionPct}
            onChange={(e) => setPositionManual(Number(e.target.value))}
            className="w-full accent-arch-green"
            aria-valuetext={frame ? displayYearLabel(frame) : ''}
          />
          <div className="mt-2 flex justify-between gap-1 text-[11px] text-arch-muted">
            {layers.map((layer, index) => {
              const tickPct = layers.length > 1 ? (index / (layers.length - 1)) * 100 : 0
              const isActive =
                Math.abs(positionPct - tickPct) < (layers.length > 1 ? 50 / (layers.length - 1) : 100)
              return (
                <button
                  key={`${layer.year}-${layer.label ?? ''}`}
                  type="button"
                  onClick={() => setPositionManual(tickPct)}
                  className={`shrink-0 rounded px-1 py-0.5 transition ${
                    isActive
                      ? 'font-semibold text-arch-green-deep'
                      : 'hover:text-arch-green-deep'
                  }`}
                >
                  {layer.label ?? layer.year}
                </button>
              )
            })}
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-arch-muted">
              {firstYear} ← ползунок → {lastYear}
            </p>
            {layers.length > 1 ? (
              <button
                type="button"
                onClick={() => setIsPlaying((playing) => !playing)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                  isPlaying
                    ? 'border-arch-green bg-arch-green-soft text-arch-green-deep'
                    : 'border-arch-line bg-arch-surface-2/60 text-arch-ink/80 hover:border-arch-green/40 hover:bg-arch-green-soft'
                }`}
                aria-pressed={isPlaying}
              >
                {isPlaying ? '⏸ Пауза' : '▶ Проиграть'}
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-arch-line bg-arch-surface p-4 shadow-sm">
        <p className="text-sm text-arch-ink/80">{stageHint}</p>
        {frame && (frame.blend >= 0.5 ? frame.to.sourceUrl : frame.from.sourceUrl) ? (
          <p className="mt-2 text-xs text-arch-muted">
            Источник:{' '}
            <a
              href={(frame.blend >= 0.5 ? frame.to.sourceUrl : frame.from.sourceUrl)!}
              target="_blank"
              rel="noopener noreferrer"
              className="text-arch-green underline"
            >
              {sourceLinkLabel((frame.blend >= 0.5 ? frame.to.sourceUrl : frame.from.sourceUrl)!)}
            </a>
          </p>
        ) : null}
      </div>
    </div>
  )
}
