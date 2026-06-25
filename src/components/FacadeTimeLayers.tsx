import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import type { Building } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import {
  buildFacadeTimeLayerStack,
  fetchExplorerManifest,
  type FacadeTimeLayerStack,
  type FacadeTimeSnapshot,
} from '../data/explorer/explorerManifest'
import {
  computeStackedAutoplayFrame,
  stackedAutoplayCycleMs,
  stackedAutoplayYearLabel,
  usesStackedAutoplay,
} from '../lib/facadeTimeLayersAutoplay'

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

/** Длительность плавного перехода между соседними кадрами (без пауз). */
const LAYER_CROSSFADE_MS = 2200

type LayerDisplayFrame = {
  from: FacadeTimeSnapshot
  to: FacadeTimeSnapshot
  fromOpacity: number
  toOpacity: number
  sliderPct: number
}

/** Плавное ускорение/замедление (smoothstep). */
function easeInOut(t: number): number {
  const x = Math.max(0, Math.min(1, t))
  return x * x * (3 - 2 * x)
}

function transitionOpacities(transitionElapsedMs: number): { fromOpacity: number; toOpacity: number } {
  const blend = easeInOut(transitionElapsedMs / LAYER_CROSSFADE_MS)
  return {
    fromOpacity: 1 - blend,
    toOpacity: blend,
  }
}

function segmentDurationMs(): number {
  return LAYER_CROSSFADE_MS
}

function autoplayCycleMs(layerCount: number): number {
  return Math.max(1, layerCount) * segmentDurationMs()
}

function sliderPctForSegment(segmentIndex: number, segmentElapsedMs: number, layerCount: number): number {
  if (layerCount <= 1) return 0
  const tickSpan = 100 / (layerCount - 1)
  const transitionProgress = Math.min(1, segmentElapsedMs / LAYER_CROSSFADE_MS)

  if (segmentIndex >= layerCount - 1) {
    return (1 - transitionProgress) * 100
  }
  return segmentIndex * tickSpan + transitionProgress * tickSpan
}

function computeAutoplayFrame(layers: FacadeTimeSnapshot[], elapsedMs: number): LayerDisplayFrame {
  if (layers.length === 1) {
    return {
      from: layers[0],
      to: layers[0],
      fromOpacity: 1,
      toOpacity: 0,
      sliderPct: 0,
    }
  }

  const cycleMs = autoplayCycleMs(layers.length)
  const cycleElapsed = ((elapsedMs % cycleMs) + cycleMs) % cycleMs
  const segmentIndex = Math.floor(cycleElapsed / segmentDurationMs())
  const segmentElapsed = cycleElapsed - segmentIndex * segmentDurationMs()
  const from = layers[segmentIndex]
  const to = layers[(segmentIndex + 1) % layers.length]
  const { fromOpacity, toOpacity } = transitionOpacities(segmentElapsed)

  return {
    from,
    to,
    fromOpacity,
    toOpacity,
    sliderPct: sliderPctForSegment(segmentIndex, segmentElapsed, layers.length),
  }
}

function manualDisplayFrame(layers: FacadeTimeSnapshot[], positionPct: number): LayerDisplayFrame {
  const crossfade = crossfadeAtPosition(layers, positionPct)
  return {
    from: crossfade.from,
    to: crossfade.to,
    fromOpacity: 1 - crossfade.blend,
    toOpacity: crossfade.blend,
    sliderPct: positionPct,
  }
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

/** Слои времени: плавный переход между снимками через затемнение (crossfade). */
export function FacadeTimeLayers({ building, archiview }: Props) {
  const [stack, setStack] = useState<FacadeTimeLayerStack | null>(null)
  const [manifestLoaded, setManifestLoaded] = useState(false)
  const [positionPct, setPositionPct] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackElapsedMs, setPlaybackElapsedMs] = useState(0)
  const playbackAnchorRef = useRef(0)
  const rafRef = useRef<number>(0)

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
      setPositionPct(0)
      setPlaybackElapsedMs(0)
      setIsPlaying(false)
      setManifestLoaded(true)
    })

    return () => {
      cancelled = true
    }
  }, [archiview.cardId])

  const layers = stack?.layers ?? []
  const stackedAutoplay = usesStackedAutoplay(archiview.cardId, layers.length)

  useEffect(() => {
    if (!isPlaying || layers.length < 2) return

    playbackAnchorRef.current = performance.now() - playbackElapsedMs

    const step = (now: number) => {
      const elapsed = now - playbackAnchorRef.current
      const frame = stackedAutoplay
        ? computeStackedAutoplayFrame(layers, elapsed)
        : computeAutoplayFrame(layers, elapsed)
      setPlaybackElapsedMs(elapsed)
      setPositionPct(frame.sliderPct)
      rafRef.current = requestAnimationFrame(step)
    }

    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
  }, [isPlaying, layers, stackedAutoplay, archiview.cardId])

  const stackedFrame = useMemo(() => {
    if (!stackedAutoplay || !isPlaying || layers.length < 4) return null
    return computeStackedAutoplayFrame(layers, playbackElapsedMs)
  }, [stackedAutoplay, isPlaying, layers, playbackElapsedMs, archiview.cardId])

  const displayFrame = useMemo(() => {
    if (!layers.length) return null
    if (isPlaying && layers.length >= 2) {
      if (stackedAutoplay) {
        const stacked = computeStackedAutoplayFrame(layers, playbackElapsedMs)
        const emphasis = layers[stacked.emphasisIndex] ?? layers[0]
        return {
          from: emphasis,
          to: emphasis,
          fromOpacity: 1,
          toOpacity: 0,
          sliderPct: stacked.sliderPct,
          sliderThumbOpacity: stacked.sliderThumbOpacity,
          stackedOpacities: stacked.opacities,
        }
      }
      const frame = computeAutoplayFrame(layers, playbackElapsedMs)
      return { ...frame, sliderThumbOpacity: 1, stackedOpacities: null as number[] | null }
    }
    const manual = manualDisplayFrame(layers, positionPct)
    return { ...manual, sliderThumbOpacity: 1, stackedOpacities: null as number[] | null }
  }, [isPlaying, layers, playbackElapsedMs, positionPct, stackedAutoplay, archiview.cardId])

  const frame = displayFrame
    ? {
        from: displayFrame.from,
        to: displayFrame.to,
        blend: displayFrame.toOpacity,
      }
    : null

  const fromOpacity = displayFrame?.fromOpacity ?? 1
  const toOpacity = displayFrame?.toOpacity ?? 0

  const stageHint = useMemo(() => {
    if (!displayFrame) return ''
    if (stackedFrame) {
      return layerHint(
        layers[stackedFrame.emphasisIndex]?.year ?? layers[0].year,
        building.id,
        layers[stackedFrame.emphasisIndex]?.label,
      )
    }
    const year = toOpacity >= 0.5 ? displayFrame.to.year : displayFrame.from.year
    const label = toOpacity >= 0.5 ? displayFrame.to.label : displayFrame.from.label
    return layerHint(year, building.id, label)
  }, [displayFrame, stackedFrame, layers, building.id, toOpacity])

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
  const cycleSeconds = Math.round(
    (stackedAutoplay
      ? stackedAutoplayCycleMs(archiview.cardId!, layers.length)
      : autoplayCycleMs(layers.length)) / 1000,
  )

  const sliderYearLabel = stackedFrame
    ? stackedAutoplayYearLabel(layers, stackedFrame.emphasisIndex)
    : frame
      ? displayYearLabel(frame)
      : ''

  const sliderThumbOpacity = displayFrame?.sliderThumbOpacity ?? 1
  const stackedOpacities = displayFrame?.stackedOpacities

  return (
    <div className="space-y-4">
      <p className="text-sm text-arch-muted">
        {stackedAutoplay ? (
          <>
            Двигайте ползунок по годам или запустите автопроигрывание. В режиме слайд-шоу: 1840
            на 100%, через 1 с одновременно с появлением 1924 уходит на 20%, 1924 — на 80%;
            затем 1930 до 80%; когда 1930 наполовину проявился — начинает появляться 2026 до 100%.
            Полный цикл ~{cycleSeconds} с.
          </>
        ) : (
          <>
            Двигайте ползунок по годам — снимки сменяют друг друга через плавное затемнение. Можно
            запустить автопроигрывание: кадры сменяют друг друга непрерывно, без остановок
            (плавный cross-dissolve ~{Math.round(LAYER_CROSSFADE_MS / 1000)} с на переход; полный цикл
            ~{cycleSeconds} с). Порядок:{' '}
            {layers.map((layer) => layer.label ?? layer.year).join(' → ')} → {firstYear}.
          </>
        )}
      </p>

      <div className="overflow-hidden rounded-2xl border border-arch-line bg-arch-green-deep shadow-md">
        <div className="relative aspect-[4/3] max-h-[min(70vh,640px)] w-full bg-arch-green-deep">
          {stackedOpacities ? (
            layers.map((layer, index) => (
              <img
                key={`${layer.year}-${layer.label ?? ''}`}
                src={layer.historicalUrl}
                alt={`Фасад ${layer.label ?? layer.year}`}
                className="absolute inset-0 h-full w-full object-contain"
                style={{ opacity: stackedOpacities[index] ?? 0 }}
              />
            ))
          ) : frame ? (
            <>
              <img
                src={frame.from.historicalUrl}
                alt={`Фасад ${frame.from.label ?? frame.from.year}`}
                className={`absolute inset-0 h-full w-full object-contain ${
                  isPlaying ? '' : 'transition-opacity duration-200'
                }`}
                style={{ opacity: fromOpacity }}
              />
              <img
                src={frame.to.historicalUrl}
                alt={`Фасад ${frame.to.label ?? frame.to.year}`}
                className={`pointer-events-none absolute inset-0 h-full w-full object-contain ${
                  isPlaying ? '' : 'transition-opacity duration-200'
                }`}
                style={{ opacity: toOpacity }}
              />
            </>
          ) : null}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/50 to-transparent" />
          <div className="absolute left-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs text-white backdrop-blur-sm">
            {sliderYearLabel}
          </div>
        </div>

        <div className="border-t border-arch-line/40 bg-arch-surface px-3 py-3 text-sm">
          <span className="mb-2 flex items-center justify-between text-arch-ink/80">
            <span>Год на шкале</span>
            <span className="font-semibold tabular-nums text-arch-green-deep">
              {sliderYearLabel}
            </span>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={0.5}
            value={positionPct}
            onChange={(e) => setPositionManual(Number(e.target.value))}
            className="time-layers-range w-full accent-arch-green"
            style={{ '--thumb-opacity': sliderThumbOpacity } as CSSProperties}
            aria-valuetext={sliderYearLabel}
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
                onClick={() => {
                  if (isPlaying) {
                    stopAutoplay()
                    return
                  }
                  playbackAnchorRef.current = performance.now() - playbackElapsedMs
                  setIsPlaying(true)
                }}
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
        {frame && !stackedOpacities && (frame.blend >= 0.5 ? frame.to.sourceUrl : frame.from.sourceUrl) ? (
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
