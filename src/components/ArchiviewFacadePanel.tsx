import { useCallback, useEffect, useState } from 'react'
import type { ArchiviewAnnotation, ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import {
  polygonCentroid,
  toPercentPoints,
  transformPolygon,
  type Point,
} from '../lib/archiviewGeometry'

type DisplayRegion = {
  idx: number
  cls: string
  label: string
  comment: string
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

export function ArchiviewFacadePanel({ assets }: { assets: ArchiviewBuildingAssets }) {
  const [regions, setRegions] = useState<DisplayRegion[]>([])
  const [imageOk, setImageOk] = useState(false)
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)
  const [imgSize, setImgSize] = useState({ w: 1, h: 1 })

  const buildRegions = useCallback(
    (annotations: ArchiviewAnnotation[], H: number[][], width: number, height: number) => {
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const raw = ann.polygon as Point[] | undefined
        if (!raw || raw.length < 3) return
        const onPhoto = transformPolygon(H, raw)
        const pct = toPercentPoints(onPhoto, width, height)
        const [cx, cy] = polygonCentroid(pct)
        list.push({
          idx: i + 1,
          cls: ann.class,
          label: ann.label_ru || ann.class,
          comment: (ann.comment || '').trim(),
          polygonPct: pct,
          cx,
          cy,
        })
      })
      setRegions(list)
    },
    [],
  )

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      const [annRes, projRes] = await Promise.all([
        fetch(assets.annotationsUrl),
        fetch(assets.facadeProjectUrl),
      ])
      const annData = annRes.ok ? await annRes.json() : null
      const projData = projRes.ok ? await projRes.json() : null
      const H = projData?.H_rect_to_modern as number[][] | undefined
      const annotations = (annData?.annotations ?? []) as ArchiviewAnnotation[]

      const img = new Image()
      img.onload = () => {
        if (cancelled) return
        setImgSize({ w: img.naturalWidth, h: img.naturalHeight })
        setImageOk(true)
        if (H && annotations.length) {
          buildRegions(annotations, H, img.naturalWidth, img.naturalHeight)
        }
      }
      img.onerror = () => {
        if (!cancelled) setImageOk(false)
      }
      img.src = assets.markedFacadeUrl
    }

    load()
    return () => {
      cancelled = true
    }
  }, [assets, buildRegions])

  const active = hoverIdx !== null ? regions.find((r) => r.idx === hoverIdx) : null

  return (
    <div className="space-y-3">
      <p className="text-sm text-arch-muted">
        Наведите на <strong>номер или область</strong> на фото — сверху появится название. Список
        справа синхронизирован с подсветкой.
      </p>

      {!imageOk && (
        <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
          Файл разметки пока не на сайте. Экспортируйте из Archiview → <code>copy_to_website.bat</code>{' '}
          → Push.
        </p>
      )}

      {imageOk && (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
          <div className="relative min-w-0 flex-1">
            <div className="relative inline-block max-w-full">
              <img
                src={assets.markedFacadeUrl}
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
                  {regions.map((r) => (
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
                    />
                  ))}
                </svg>
              )}
              {active && (
                <div
                  className="pointer-events-none absolute z-20 max-w-[min(92%,280px)] rounded-md border border-arch-gold bg-arch-surface px-2.5 py-1.5 text-center text-xs font-semibold leading-snug text-arch-ink shadow-lg"
                  style={{
                    left: `${active.cx}%`,
                    top: `${active.cy}%`,
                    transform: 'translate(-50%, calc(-100% - 8px))',
                  }}
                >
                  <span className="text-[11px] font-bold text-arch-green">{active.idx}.</span>{' '}
                  {active.label}
                  {active.comment ? (
                    <span className="mt-0.5 block text-[10px] font-normal text-arch-muted">
                      {active.comment}
                    </span>
                  ) : null}
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
                      className={`flex w-full gap-2 rounded-lg border px-2.5 py-2 text-left transition ${
                        on
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
                          {r.label}
                        </span>
                        {r.comment ? (
                          <span className="mt-0.5 block text-xs text-arch-muted">{r.comment}</span>
                        ) : null}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
