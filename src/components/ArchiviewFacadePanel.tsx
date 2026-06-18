import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ArchiviewAnnotation, ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import type { Building, MemoryTrace } from '../types/building'
import { ConfidenceBadge } from './ConfidenceBadge'
import {
  polygonAreaAbs,
  polygonCentroid,
  rectifiedPolygonToComparison,
  toPercentPoints,
  transformPolygon,
  type Point,
} from '../lib/archiviewGeometry'

type DisplayRegion = {
  idx: number
  cls: string
  label: string
  comment: string
  trace?: MemoryTrace
  polygonPct: Point[]
  cx: number
  cy: number
}

const CLASS_COLORS: Record<string, string> = {
  added_floor: '#00aa00',
  extension: '#ff8c00',
  filled_window: '#0078d7',
  new_window: '#00aaaa',
  lost_balcony: '#b850b0',
  new_balcony: '#d08a00',
  changed_entrance: '#786cff',
  lost_decor: '#aa50ff',
  historical_signage: '#2896c8',
  lost_signage: '#c83c78',
  signage_rediscovered: '#ffc800',
  restored_signage: '#3cc83c',
  new_signage: '#ff8200',
  memorial_plaque: '#a07850',
  technical_artifact: '#7a8a00',
  other_artifact: '#8a8a00',
  check_manually: '#b000b0',
}

type AnnPayload = {
  annotations?: ArchiviewAnnotation[]
  labeling_layout?: string
  side_by_side?: Record<string, unknown>
  rectified_size?: { width?: number; height?: number }
}

function imageMatchesRectifiedSize(
  width: number,
  height: number,
  rectified?: { width?: number; height?: number },
): boolean {
  if (!rectified?.width || !rectified?.height) return false
  return Math.abs(width - rectified.width) <= 2 && Math.abs(height - rectified.height) <= 2
}

function isHomography(H: unknown): H is number[][] {
  return (
    Array.isArray(H) &&
    H.length === 3 &&
    H.every(
      (row) =>
        Array.isArray(row) &&
        row.length === 3 &&
        row.every((value) => typeof value === 'number' && Number.isFinite(value)),
    )
  )
}

function getTraceId(ann: ArchiviewAnnotation): string | undefined {
  return ann.traceId
}

function shortText(text: string, maxLength = 260): string {
  if (text.length <= maxLength) return text
  const shortened = text.slice(0, maxLength)
  const sentenceEnd = Math.max(shortened.lastIndexOf('.'), shortened.lastIndexOf('!'), shortened.lastIndexOf('?'))
  if (sentenceEnd > maxLength * 0.55) return shortened.slice(0, sentenceEnd + 1)
  return `${shortened.trim()}...`
}

export function ArchiviewFacadePanel({
  assets,
  building,
}: {
  assets: ArchiviewBuildingAssets
  building?: Building
}) {
  const [regions, setRegions] = useState<DisplayRegion[]>([])
  const [imageOk, setImageOk] = useState(false)
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const [imgSize, setImgSize] = useState({ w: 1, h: 1 })
  const [sideBySide, setSideBySide] = useState(false)

  const tracesById = useMemo(() => {
    return new Map(building?.memoryTraces.map((trace) => [trace.id, trace]) ?? [])
  }, [building])

  const displayImageUrl = useMemo(() => {
    if (assets.labelingLayout === 'side_by_side' && assets.sideBySideMarkedUrl) {
      return assets.sideBySideMarkedUrl
    }
    return assets.markedFacadeUrl
  }, [assets])

  const makeRegion = useCallback(
    (ann: ArchiviewAnnotation, idx: number, polygonPct: Point[]): DisplayRegion => {
      const [cx, cy] = polygonCentroid(polygonPct)
      const traceId = getTraceId(ann)
      return {
        idx,
        cls: ann.class,
        label: ann.label_ru || ann.class,
        comment: (ann.comment || '').trim(),
        trace: traceId ? tracesById.get(traceId) : undefined,
        polygonPct,
        cx,
        cy,
      }
    },
    [tracesById],
  )

  const buildRegionsRectified = useCallback(
    (annotations: ArchiviewAnnotation[], width: number, height: number) => {
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const raw = ann.polygon as Point[] | undefined
        if (!raw || raw.length < 3) return
        const pct = toPercentPoints(raw, width, height)
        list.push(makeRegion(ann, i + 1, pct))
      })
      setRegions(list)
    },
    [makeRegion],
  )

  const buildRegionsOverlay = useCallback(
    (annotations: ArchiviewAnnotation[], H: number[][], width: number, height: number) => {
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const raw = ann.polygon as Point[] | undefined
        if (!raw || raw.length < 3) return
        const onPhoto = transformPolygon(H, raw)
        const pct = toPercentPoints(onPhoto, width, height)
        list.push(makeRegion(ann, i + 1, pct))
      })
      setRegions(list)
    },
    [makeRegion],
  )

  const buildRegionsSideBySide = useCallback(
    (
      annotations: ArchiviewAnnotation[],
      payload: AnnPayload,
      width: number,
      height: number,
    ) => {
      const sb = payload.side_by_side ?? {}
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const raw = ann.polygon as Point[] | undefined
        if (!raw || raw.length < 3) return
        const side =
          (ann as ArchiviewAnnotation & { image_side?: string }).image_side === 'historical'
            ? 'historical'
            : 'modern'
        const onPanel = rectifiedPolygonToComparison(
          raw,
          side,
          sb as Parameters<typeof rectifiedPolygonToComparison>[2],
          payload.rectified_size,
        )
        const pct = toPercentPoints(onPanel, width, height)
        list.push(makeRegion(ann, i + 1, pct))
      })
      setRegions(list)
    },
    [makeRegion],
  )

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      const [annRes, projRes] = await Promise.all([
        fetch(assets.annotationsUrl),
        fetch(assets.facadeProjectUrl),
      ])
      const annData = (annRes.ok ? await annRes.json() : null) as AnnPayload | null
      const projData = projRes.ok ? await projRes.json() : null
      const H = isHomography(projData?.H_rect_to_modern) ? projData.H_rect_to_modern : undefined
      const annotations = (annData?.annotations ?? []) as ArchiviewAnnotation[]
      const explicitLayout = annData?.labeling_layout ?? assets.labelingLayout
      const layout = explicitLayout ?? 'legacy_overlay'
      const isSb = layout === 'side_by_side'
      if (!cancelled) setSideBySide(isSb)

      const img = new Image()
      img.onload = () => {
        if (cancelled) return
        setImgSize({ w: img.naturalWidth, h: img.naturalHeight })
        setImageOk(true)
        if (!annotations.length) {
          setRegions([])
          return
        }
        if (isSb && annData?.side_by_side) {
          buildRegionsSideBySide(annotations, annData, img.naturalWidth, img.naturalHeight)
        } else if (!isSb && imageMatchesRectifiedSize(img.naturalWidth, img.naturalHeight, annData?.rectified_size)) {
          buildRegionsRectified(annotations, img.naturalWidth, img.naturalHeight)
        } else if (H) {
          buildRegionsOverlay(annotations, H, img.naturalWidth, img.naturalHeight)
        } else if (!isSb && explicitLayout === 'overlay' && !annData?.rectified_size) {
          buildRegionsRectified(annotations, img.naturalWidth, img.naturalHeight)
        } else {
          setRegions([])
        }
      }
      img.onerror = () => {
        if (!cancelled) setImageOk(false)
      }
      img.src = displayImageUrl
    }

    load()
    return () => {
      cancelled = true
    }
  }, [assets, buildRegionsOverlay, buildRegionsRectified, buildRegionsSideBySide, displayImageUrl])

  const active =
    hoverIdx !== null
      ? regions.find((r) => r.idx === hoverIdx)
      : selectedIdx !== null
        ? regions.find((r) => r.idx === selectedIdx)
        : null
  const selected = selectedIdx !== null ? regions.find((r) => r.idx === selectedIdx) : null

  /** Large regions (e.g. #12) must not block clicks on smaller ones (#6, #9) underneath. */
  const regionsForHit = useMemo(
    () => [...regions].sort((a, b) => polygonAreaAbs(a.polygonPct) - polygonAreaAbs(b.polygonPct)),
    [regions],
  )

  return (
    <div className="space-y-3">
      <p className="text-sm text-arch-muted">
        {sideBySide ? (
          <>
            Слева — историческое фото, справа — современное. Наведите на <strong>номер или область</strong>{' '}
            — сверху появится кураторская плашка.
          </>
        ) : (
          <>
            Наведите или нажмите на <strong>номер или область</strong> на фото — сверху появится
            кураторская плашка. Список справа синхронизирован с подсветкой.
          </>
        )}
      </p>

      {!imageOk && (
        <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
          Файл разметки пока не на сайте. Экспортируйте из Archiview → <code>copy_to_website.bat</code>{' '}
          (CardId: {assets.cardId}) → Push → Ctrl+F5.
        </p>
      )}

      {imageOk && (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
          <div className="relative min-w-0 flex-1">
            <div
              className="relative inline-block max-w-full"
              onMouseLeave={() => setHoverIdx(null)}
            >
              <img
                src={displayImageUrl}
                alt="Фасад с разметкой Archiview"
                width={imgSize.w}
                height={imgSize.h}
                className="block max-h-[min(78vh,820px)] w-full rounded-xl border border-arch-line object-contain shadow-sm"
              />
              {regions.length > 0 && (
                <svg
                  className="pointer-events-none absolute inset-0 h-full w-full rounded-xl"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                  aria-hidden
                >
                  {regions.map((r) => {
                    const on = hoverIdx === r.idx
                    return (
                      <polygon
                        key={r.idx}
                        points={r.polygonPct.map(([x, y]) => `${x},${y}`).join(' ')}
                        fill={on ? 'rgba(251,191,36,0.42)' : 'transparent'}
                        stroke={on ? '#d97706' : 'transparent'}
                        strokeWidth={on ? 0.45 : 0}
                      />
                    )
                  })}
                </svg>
              )}
              {regions.length > 0 && (
                <svg
                  className="absolute inset-0 h-full w-full rounded-xl"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                >
                  {regionsForHit.map((r) => (
                    <polygon
                      key={`hit-${r.idx}`}
                      points={r.polygonPct.map(([x, y]) => `${x},${y}`).join(' ')}
                      fill="transparent"
                      stroke="transparent"
                      className="cursor-pointer"
                      onMouseEnter={() => setHoverIdx(r.idx)}
                      onMouseLeave={() => setHoverIdx(null)}
                      onFocus={() => setHoverIdx(r.idx)}
                      onBlur={() => setHoverIdx(null)}
                      onClick={() => setSelectedIdx((current) => (current === r.idx ? null : r.idx))}
                    />
                  ))}
                </svg>
              )}
              {active && (
                <div
                  className="pointer-events-none absolute z-20 max-w-[min(92%,360px)] rounded-xl border border-arch-gold/70 bg-arch-green-deep/90 px-3 py-2.5 text-left text-xs leading-snug text-arch-surface shadow-xl backdrop-blur-md"
                  style={{
                    left: `${active.cx}%`,
                    top: `${active.cy}%`,
                    transform: 'translate(-50%, calc(-100% - 8px))',
                  }}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-arch-gold text-[11px] font-bold text-arch-green-deep">
                      {active.idx}
                    </span>
                    <span>
                      <span className="block font-semibold">{active.trace?.title ?? active.label}</span>
                      {active.trace ? (
                        <>
                          <span className="mt-0.5 block text-[11px] text-arch-surface/75">
                            {active.trace.period}
                          </span>
                          <span className="mt-1 block text-[11px] font-normal text-arch-surface/90">
                            {shortText(active.trace.userMessage)}
                          </span>
                        </>
                      ) : active.comment ? (
                        <span className="mt-1 block text-[11px] font-normal text-arch-surface/80">
                          {active.comment}
                        </span>
                      ) : null}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {regions.length > 0 && (
            <ol className="w-full shrink-0 space-y-1.5 text-sm lg:w-64 xl:w-72">
              {regions.map((r) => {
                const on = hoverIdx === r.idx
                const color = CLASS_COLORS[r.cls] ?? '#444'
                return (
                  <li key={r.idx}>
                    <button
                      type="button"
                      onMouseEnter={() => setHoverIdx(r.idx)}
                      onMouseLeave={() => setHoverIdx(null)}
                      onFocus={() => setHoverIdx(r.idx)}
                      onBlur={() => setHoverIdx(null)}
                      onClick={() => setSelectedIdx((current) => (current === r.idx ? null : r.idx))}
                      className={`flex w-full gap-2 rounded-lg border px-2.5 py-2 text-left transition ${
                        on || selectedIdx === r.idx
                          ? 'border-arch-green/50 bg-arch-green-soft shadow-sm'
                          : 'border-arch-line bg-arch-surface hover:border-arch-green/30'
                      }`}
                    >
                      <span
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                        style={{ background: color }}
                      >
                        {r.idx}
                      </span>
                      <span className="min-w-0">
                        <span className="block font-medium leading-tight text-arch-ink">
                          {r.trace?.title ?? r.label}
                        </span>
                        {r.trace ? (
                          <span className="mt-0.5 block text-xs text-arch-muted">
                            {r.trace.period} · кураторская заметка
                          </span>
                        ) : r.comment ? (
                          <span className="mt-0.5 block text-xs text-arch-muted">{r.comment}</span>
                        ) : null}
                      </span>
                    </button>
                  </li>
                )
              })}
              {selected?.trace && (
                <li className="rounded-xl border border-arch-green/25 bg-arch-green-soft p-3">
                  <p className="arch-kicker mb-1">Информация от куратора</p>
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold leading-tight text-arch-green-deep">
                      {selected.trace.title}
                    </h3>
                    <ConfidenceBadge level={selected.trace.confidence} />
                  </div>
                  <p className="text-xs text-arch-muted">{selected.trace.period}</p>
                  <p className="mt-2 text-sm leading-relaxed text-arch-ink/80">
                    {selected.trace.userMessage}
                  </p>
                </li>
              )}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
