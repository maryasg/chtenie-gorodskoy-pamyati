import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ArchiviewAnnotation, ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'
import type { Building, MemoryTrace } from '../types/building'
import {
  homographyRectToFullSource,
  polygonAreaAbs,
  polygonCentroid,
  rectifiedPolygonToComparison,
  shiftPolygon,
  sourceCropOffsetFromProject,
  toPercentPoints,
  transformPolygon,
  type Point,
} from '../lib/archiviewGeometry'
import { ExpertTracePlate } from './ExpertTracePlate'
import { tracePlatePlacement } from '../lib/tracePlatePlacement'
import { computeBadgeLayout, assignBadgeLayouts, type BadgeLayout } from '../lib/regionBadgeLayout'

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

/** Окна и узкие проёмы: без сплошной заливки-квадрата — только контур и кружок. */
const COMPACT_REGION_AREA = 90

type DisplayRegion = {
  idx: number
  cls: string
  label: string
  comment: string
  trace?: MemoryTrace
  polygonPct: Point[]
  cx: number
  cy: number
  areaPct: number
  badgeLayout: BadgeLayout
}

function regionPolygonStyle(
  color: string,
  area: number,
  on: boolean,
  arIdle = false,
): { fill: string; strokeWidth: number } {
  if (arIdle && !on) {
    return {
      fill: `${color}28`,
      strokeWidth: 0.45,
    }
  }
  if (area < COMPACT_REGION_AREA) {
    return {
      fill: 'none',
      strokeWidth: on ? 0.8 : 0.58,
    }
  }
  return {
    fill: on ? `${color}66` : `${color}40`,
    strokeWidth: on ? 0.55 : 0.35,
  }
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

function annotationDisplayIndex(ann: ArchiviewAnnotation, arrayIndex: number): number {
  const id = ann.id
  if (typeof id === 'number' && Number.isFinite(id) && id > 0) return id
  return arrayIndex + 1
}

type FacadeImageKind = 'side_by_side' | 'source_modern' | 'rectified' | 'marked'

const ZOOM_MIN = 1
const ZOOM_MAX = 4
const ZOOM_STEP = 0.35

type Pan = { x: number; y: number }

function clampZoom(value: number): number {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, value))
}

function panForZoomAtCenter(
  pan: Pan,
  zoom: number,
  nextZoom: number,
  centerX: number,
  centerY: number,
): Pan {
  if (nextZoom <= ZOOM_MIN) return { x: 0, y: 0 }
  const cx = (centerX - pan.x) / zoom
  const cy = (centerY - pan.y) / zoom
  return {
    x: centerX - cx * nextZoom,
    y: centerY - cy * nextZoom,
  }
}

type ImageProbe = { w: number; h: number; bytes: number }

async function probeImageMeta(url: string): Promise<ImageProbe | null> {
  let bytes = 0
  try {
    const head = await fetch(url, { method: 'HEAD', cache: 'no-cache' })
    if (!head.ok) return null
    bytes = Number(head.headers.get('content-length') || 0)
  } catch {
    return null
  }
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight, bytes })
    img.onerror = () => resolve(null)
    img.src = url
  })
}

/**
 * Фон фасада: чистое фото без запечённой разметки.
 * Номера и цветные зоны рисует панель поверх (кружки — HTML, полигоны — SVG).
 */
async function pickFacadeImage(
  assets: ArchiviewBuildingAssets,
  options?: {
    arMode?: boolean
    hasArHomography?: boolean
    preferRectified?: boolean
    /** AR: modern-source + polygon_source, если полевое фото ещё без crop/H_ar */
    preferAlignedSource?: boolean
  },
): Promise<{ url: string; kind: FacadeImageKind; w: number; h: number } | null> {
  if (options?.arMode) {
    if (options.hasArHomography && assets.arPhotoUrl) {
      const arPhoto = await probeImageMeta(assets.arPhotoUrl)
      if (arPhoto) {
        return { url: assets.arPhotoUrl, kind: 'source_modern', w: arPhoto.w, h: arPhoto.h }
      }
    }

    if (options.preferAlignedSource && assets.modernSourceUrl) {
      const source = await probeImageMeta(assets.modernSourceUrl)
      if (source) {
        return { url: assets.modernSourceUrl, kind: 'source_modern', w: source.w, h: source.h }
      }
    }

    if (assets.arPhotoUrl) {
      const arPhoto = await probeImageMeta(assets.arPhotoUrl)
      if (arPhoto) {
        return { url: assets.arPhotoUrl, kind: 'source_modern', w: arPhoto.w, h: arPhoto.h }
      }
    }

    if (assets.modernSourceUrl) {
      const source = await probeImageMeta(assets.modernSourceUrl)
      if (source) {
        return { url: assets.modernSourceUrl, kind: 'source_modern', w: source.w, h: source.h }
      }
    }

    if (assets.modernRectifiedUrl) {
      const rectified = await probeImageMeta(assets.modernRectifiedUrl)
      if (rectified) {
        return { url: assets.modernRectifiedUrl, kind: 'rectified', w: rectified.w, h: rectified.h }
      }
    }

    return null
  }

  if (options?.preferRectified && assets.modernRectifiedUrl) {
    const rectified = await probeImageMeta(assets.modernRectifiedUrl)
    if (rectified) {
      return { url: assets.modernRectifiedUrl, kind: 'rectified', w: rectified.w, h: rectified.h }
    }
  }

  if (assets.labelingLayout === 'side_by_side' && assets.sideBySideMarkedUrl) {
    const sb = await probeImageMeta(assets.sideBySideMarkedUrl)
    return sb ? { url: assets.sideBySideMarkedUrl, kind: 'side_by_side', w: sb.w, h: sb.h } : null
  }

  if (assets.modernSourceUrl) {
    const source = await probeImageMeta(assets.modernSourceUrl)
    if (source) {
      return { url: assets.modernSourceUrl, kind: 'source_modern', w: source.w, h: source.h }
    }
  }

  const rectifiedUrl = assets.modernRectifiedUrl
  if (rectifiedUrl) {
    const rectified = await probeImageMeta(rectifiedUrl)
    if (rectified) {
      return { url: rectifiedUrl, kind: 'rectified', w: rectified.w, h: rectified.h }
    }
  }

  const markedUrl = assets.markedFacadeUrl
  if (markedUrl) {
    const marked = await probeImageMeta(markedUrl)
    if (marked) return { url: markedUrl, kind: 'marked', w: marked.w, h: marked.h }
  }
  return null
}

function annotationHasSourcePolygon(ann: ArchiviewAnnotation): boolean {
  const raw = ann.polygon_source as Point[] | undefined
  return Boolean(raw && raw.length >= 3)
}

function annotationsHaveSourcePolygons(annotations: ArchiviewAnnotation[]): boolean {
  return annotations.some(annotationHasSourcePolygon)
}

export function ArchiviewFacadePanel({
  assets,
  building,
  variant = 'default',
  embeddedAr = false,
  hideIntro = false,
}: {
  assets: ArchiviewBuildingAssets
  building?: Building
  variant?: 'default' | 'ar'
  /** Внутри рамки телефона в AR-симуляции */
  embeddedAr?: boolean
  /** Скрыть подпись (её рисует FacadeARPreview внутри экрана) */
  hideIntro?: boolean
}) {
  const [regions, setRegions] = useState<DisplayRegion[]>([])
  const [imageOk, setImageOk] = useState(false)
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const [imgSize, setImgSize] = useState({ w: 1, h: 1 })
  const [sideBySide, setSideBySide] = useState(false)
  const [displayImageUrl, setDisplayImageUrl] = useState('')
  const [imageKind, setImageKind] = useState<FacadeImageKind | null>(null)
  const [zoom, setZoom] = useState(ZOOM_MIN)
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const viewportRef = useRef<HTMLDivElement>(null)
  const panSessionRef = useRef<{ startPan: Pan; startX: number; startY: number; moved: boolean } | null>(
    null,
  )

  const resetView = useCallback(() => {
    setZoom(ZOOM_MIN)
    setPan({ x: 0, y: 0 })
  }, [])

  const viewportCenter = useCallback((): { x: number; y: number } => {
    const el = viewportRef.current
    if (!el) return { x: 0, y: 0 }
    const rect = el.getBoundingClientRect()
    return { x: rect.width / 2, y: rect.height / 2 }
  }, [])

  const zoomIn = useCallback(() => {
    setZoom((current) => {
      const next = clampZoom(Number((current + ZOOM_STEP).toFixed(2)))
      if (next === current) return current
      const center = viewportCenter()
      setPan((p) => panForZoomAtCenter(p, current, next, center.x, center.y))
      return next
    })
  }, [viewportCenter])

  const zoomOut = useCallback(() => {
    setZoom((current) => {
      const next = clampZoom(Number((current - ZOOM_STEP).toFixed(2)))
      if (next === current) return current
      if (next <= ZOOM_MIN) {
        setPan({ x: 0, y: 0 })
        return ZOOM_MIN
      }
      const center = viewportCenter()
      setPan((p) => panForZoomAtCenter(p, current, next, center.x, center.y))
      return next
    })
  }, [viewportCenter])

  const handleViewportPointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (zoom <= ZOOM_MIN || event.button !== 0) return
      const target = event.target as HTMLElement
      if (target.closest('button') || target.tagName === 'polygon') return
      panSessionRef.current = {
        startPan: pan,
        startX: event.clientX,
        startY: event.clientY,
        moved: false,
      }
      setIsPanning(true)
      event.currentTarget.setPointerCapture(event.pointerId)
    },
    [pan, zoom],
  )

  const handleViewportPointerMove = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const session = panSessionRef.current
    if (!session) return
    const dx = event.clientX - session.startX
    const dy = event.clientY - session.startY
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) session.moved = true
    setPan({
      x: session.startPan.x + dx,
      y: session.startPan.y + dy,
    })
  }, [])

  const endPanSession = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    if (panSessionRef.current) {
      panSessionRef.current = null
      setIsPanning(false)
      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId)
      }
    }
  }, [])

  const tracesById = useMemo(() => {
    return new Map(building?.memoryTraces.map((trace) => [trace.id, trace]) ?? [])
  }, [building])

  const makeRegion = useCallback(
    (ann: ArchiviewAnnotation, idx: number, polygonPct: Point[]): DisplayRegion => {
      const [cx, cy] = polygonCentroid(polygonPct)
      const areaPct = polygonAreaAbs(polygonPct)
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
        areaPct,
        badgeLayout: computeBadgeLayout(polygonPct, areaPct, idx, assets.cardId),
      }
    },
    [assets.cardId, tracesById],
  )

  const publishRegions = useCallback(
    (list: DisplayRegion[]) => {
      assignBadgeLayouts(list, assets.cardId)
      setRegions(list)
    },
    [assets.cardId],
  )

  const buildRegionsRectified = useCallback(
    (annotations: ArchiviewAnnotation[], width: number, height: number) => {
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const raw = ann.polygon as Point[] | undefined
        if (!raw || raw.length < 3) return
        const pct = toPercentPoints(raw, width, height)
        list.push(makeRegion(ann, annotationDisplayIndex(ann, i), pct))
      })
      publishRegions(list)
    },
    [makeRegion, publishRegions],
  )

  const buildRegionsFromSourcePolygons = useCallback(
    (
      annotations: ArchiviewAnnotation[],
      width: number,
      height: number,
      offset: Point = [0, 0],
    ) => {
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const rawBase = (ann.polygon_source ?? ann.polygon) as Point[] | undefined
        if (!rawBase || rawBase.length < 3) return
        const raw = shiftPolygon(rawBase, offset)
        const pct = toPercentPoints(raw, width, height)
        list.push(makeRegion(ann, annotationDisplayIndex(ann, i), pct))
      })
      publishRegions(list)
    },
    [makeRegion, publishRegions],
  )

  const buildRegionsOverlay = useCallback(
    (annotations: ArchiviewAnnotation[], H: number[][], width: number, height: number) => {
      const list: DisplayRegion[] = []
      annotations.forEach((ann, i) => {
        const raw = ann.polygon as Point[] | undefined
        if (!raw || raw.length < 3) return
        const onPhoto = transformPolygon(H, raw)
        const pct = toPercentPoints(onPhoto, width, height)
        list.push(makeRegion(ann, annotationDisplayIndex(ann, i), pct))
      })
      publishRegions(list)
    },
    [makeRegion, publishRegions],
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
        list.push(makeRegion(ann, annotationDisplayIndex(ann, i), pct))
      })
      publishRegions(list)
    },
    [makeRegion, publishRegions],
  )

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setImageOk(false)
      setDisplayImageUrl('')
      setImageKind(null)
      setRegions([])
      resetView()

      const [annRes, projRes] = await Promise.all([
        fetch(assets.annotationsUrl),
        fetch(assets.facadeProjectUrl),
      ])
      const annData = (annRes.ok ? await annRes.json() : null) as AnnPayload | null
      const projData = projRes.ok ? await projRes.json() : null
      const H_ar = isHomography(projData?.H_rect_to_ar) ? projData.H_rect_to_ar : undefined
      const H_modern = isHomography(projData?.H_rect_to_modern) ? projData.H_rect_to_modern : undefined
      const H_modern_full = H_modern
        ? homographyRectToFullSource(H_modern, sourceCropOffsetFromProject(projData))
        : undefined
      const cropOffset = sourceCropOffsetFromProject(projData)
      const annotations = (annData?.annotations ?? []) as ArchiviewAnnotation[]
      const layout = (annData?.labeling_layout ?? assets.labelingLayout) ?? 'legacy_overlay'
      const isSb = layout === 'side_by_side'
      if (!cancelled) setSideBySide(isSb)

      const hasArAlignment =
        Boolean(H_ar) || Math.abs(cropOffset[0]) > 0.5 || Math.abs(cropOffset[1]) > 0.5

      const loaded = await pickFacadeImage(assets, {
        arMode: variant === 'ar',
        hasArHomography: Boolean(H_ar),
        preferRectified: variant === 'default' && !isSb,
        preferAlignedSource: variant === 'ar' && !hasArAlignment,
      })
      if (cancelled) return

      if (!loaded) {
        setImageOk(false)
        return
      }

      const isArFieldPhoto =
        variant === 'ar' && Boolean(assets.arPhotoUrl) && loaded.url === assets.arPhotoUrl
      const useArHomography = isArFieldPhoto && Boolean(H_ar)
      const hasCropOffset = Math.abs(cropOffset[0]) > 0.5 || Math.abs(cropOffset[1]) > 0.5
      const useSourcePolygonsOnField =
        isArFieldPhoto &&
        hasCropOffset &&
        !useArHomography &&
        annotationsHaveSourcePolygons(annotations)
      const useFieldHomography =
        isArFieldPhoto && !useArHomography && !useSourcePolygonsOnField && Boolean(H_modern_full)
      const useSourcePolygons =
        !isSb &&
        loaded.kind === 'source_modern' &&
        !useArHomography &&
        !useFieldHomography &&
        !useSourcePolygonsOnField &&
        annotationsHaveSourcePolygons(annotations)
      const sourcePolygonOffset: Point = useSourcePolygonsOnField ? cropOffset : [0, 0]
      const H = useArHomography ? H_ar : H_modern_full

      setDisplayImageUrl(loaded.url)
      setImageKind(loaded.kind)
      setImgSize({ w: loaded.w, h: loaded.h })
      setImageOk(true)

      if (!annotations.length) {
        setRegions([])
        return
      }

      if (isSb && annData?.side_by_side) {
        buildRegionsSideBySide(annotations, annData, loaded.w, loaded.h)
      } else if (useArHomography || useFieldHomography) {
        buildRegionsOverlay(annotations, H!, loaded.w, loaded.h)
      } else if (useSourcePolygonsOnField || useSourcePolygons) {
        buildRegionsFromSourcePolygons(annotations, loaded.w, loaded.h, sourcePolygonOffset)
      } else if (!isSb && loaded.kind === 'source_modern' && H) {
        buildRegionsOverlay(annotations, H, loaded.w, loaded.h)
      } else if (
        !isSb &&
        (loaded.kind === 'rectified' ||
          imageMatchesRectifiedSize(loaded.w, loaded.h, annData?.rectified_size))
      ) {
        buildRegionsRectified(annotations, loaded.w, loaded.h)
      } else if (H) {
        buildRegionsOverlay(annotations, H, loaded.w, loaded.h)
      } else if (!isSb && !annData?.rectified_size) {
        buildRegionsRectified(annotations, loaded.w, loaded.h)
      } else {
        setRegions([])
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [
    assets,
    buildRegionsFromSourcePolygons,
    buildRegionsOverlay,
    buildRegionsRectified,
    buildRegionsSideBySide,
    resetView,
    variant,
  ])

  const plateRegion =
    selectedIdx !== null
      ? regions.find((r) => r.idx === selectedIdx) ?? null
      : hoverIdx !== null
        ? regions.find((r) => r.idx === hoverIdx) ?? null
        : null
  const plateExpanded = selectedIdx !== null && plateRegion?.idx === selectedIdx
  const platePlacement = plateRegion
    ? tracePlatePlacement(plateRegion.cy, plateExpanded)
    : null

  /** Small regions (e.g. #6, #9) must paint above large overlaps (#12) for clicks — render largest first, smallest last in SVG. */
  const regionsForHit = useMemo(
    () => [...regions].sort((a, b) => polygonAreaAbs(b.polygonPct) - polygonAreaAbs(a.polygonPct)),
    [regions],
  )

  const regionsBadges = useMemo(
    () => [...regions].sort((a, b) => polygonAreaAbs(b.polygonPct) - polygonAreaAbs(a.polygonPct)),
    [regions],
  )

  return (
    <div className={embeddedAr ? 'space-y-0' : 'space-y-3'}>
      {!hideIntro && variant === 'default' ? (
        <p className="text-sm text-arch-muted">
          {sideBySide ? (
            <>
              Слева — историческое фото, справа — современное. Наведите на <strong>номер или область</strong>{' '}
              — краткая плашка. <strong>Клик</strong> по заметке в списке или по зоне откроет полную карточку
              с текстом, источниками и достоверностью. Кнопки <strong>+</strong> / <strong>−</strong> приближают
              фото.
            </>
          ) : imageKind === 'rectified' ? (
            <>
              Выпрямленное фото с подсветкой областей. Номера и цветные зоны видны сразу; при
              наведении — краткая плашка, <strong>клик</strong> по зоне или заметке в списке — полная карточка
              с источниками и достоверностью. Кнопки <strong>+</strong> / <strong>−</strong> приближают фото;
              при увеличении можно сдвигать картинку мышью.
            </>
          ) : (
            <>
              Современное фото в исходном ракурсе с подсветкой областей. Номера и цветные зоны видны
              сразу; при наведении — краткая плашка, <strong>клик</strong> по зоне или заметке в списке —
              полная карточка с источниками и достоверностью. Кнопки <strong>+</strong> / <strong>−</strong>{' '}
              приближают фото; при увеличении можно сдвигать картинку мышью.
            </>
          )}
        </p>
      ) : !hideIntro ? (
        <p className="text-sm text-arch-surface/75">
          Исходный ракурс с улицы — как в видоискателе. Подсветка зон видна сразу;{' '}
          <strong>наведите</strong> на область — краткая подсказка. <strong>Клик</strong> — полная
          карточка по центру экрана. Цифры на фото не дублируются.
        </p>
      ) : null}

      {!imageOk && (
        <p
          className={`rounded-lg border border-dashed p-4 text-sm ${
            variant === 'ar'
              ? 'border-arch-surface/30 bg-arch-green-deep/40 text-arch-surface/75'
              : 'border-arch-line bg-arch-surface-2/60 text-arch-muted'
          }`}
        >
          {variant === 'ar' ? (
            <>
              Для AR-preview нужны полевое фото и разметка Archiview. Если подсветка съезжает —
              переэкспортируйте <code>facade-project.json</code> с <code>modern_crop_offset_xy</code>{' '}
              через <code>copy_to_website.bat</code> (CardId: {assets.cardId}).
            </>
          ) : (
            <>
              Файл разметки пока не на сайте. Экспортируйте из Archiview → <code>copy_to_website.bat</code>{' '}
              (CardId: {assets.cardId}) → Push → Ctrl+F5.
            </>
          )}
        </p>
      )}

      {imageOk && (
        <div className={`flex flex-col gap-4 ${variant === 'ar' ? '' : 'lg:flex-row lg:items-start'}`}>
          <div className={`relative min-w-0 flex-1 ${embeddedAr ? '' : ''}`}>
            <div
              ref={viewportRef}
              className={`relative w-full ${
                embeddedAr ? '' : 'shadow-sm'
              } ${
                variant === 'ar'
                  ? embeddedAr
                    ? 'h-full bg-arch-green-deep'
                    : 'rounded-lg border border-arch-surface/15 bg-arch-green-deep/80'
                  : 'rounded-xl border border-arch-line bg-arch-surface-2/20'
              } ${
                zoom > ZOOM_MIN
                  ? embeddedAr
                    ? 'h-full max-h-none overflow-hidden'
                    : 'max-h-[min(78vh,820px)] overflow-hidden'
                  : embeddedAr
                    ? 'h-full overflow-y-auto overflow-x-hidden'
                    : 'overflow-visible'
              } ${zoom > ZOOM_MIN ? (isPanning ? 'cursor-grabbing' : 'cursor-grab') : ''}`}
              onMouseLeave={() => setHoverIdx(null)}
              onPointerDown={handleViewportPointerDown}
              onPointerMove={handleViewportPointerMove}
              onPointerUp={endPanSession}
              onPointerCancel={endPanSession}
            >
              <div
                className="absolute right-2 top-2 z-30 flex items-center gap-1 rounded-lg border border-arch-line/80 bg-arch-surface/95 p-1 shadow-md backdrop-blur-sm"
                role="toolbar"
                aria-label="Масштаб фасада"
              >
                <button
                  type="button"
                  onClick={zoomOut}
                  disabled={zoom <= ZOOM_MIN}
                  aria-label="Уменьшить"
                  className="flex h-8 w-8 items-center justify-center rounded-md text-lg font-semibold text-arch-green-deep transition hover:bg-arch-green-soft disabled:cursor-not-allowed disabled:opacity-40"
                >
                  −
                </button>
                <button
                  type="button"
                  onClick={resetView}
                  disabled={zoom <= ZOOM_MIN && pan.x === 0 && pan.y === 0}
                  aria-label="Сбросить масштаб"
                  title="Сбросить"
                  className="flex h-8 min-w-8 items-center justify-center rounded-md px-1.5 text-xs font-semibold text-arch-green-deep transition hover:bg-arch-green-soft disabled:cursor-not-allowed disabled:opacity-40"
                >
                  1:1
                </button>
                <button
                  type="button"
                  onClick={zoomIn}
                  disabled={zoom >= ZOOM_MAX}
                  aria-label="Увеличить"
                  className="flex h-8 w-8 items-center justify-center rounded-md text-lg font-semibold text-arch-green-deep transition hover:bg-arch-green-soft disabled:cursor-not-allowed disabled:opacity-40"
                >
                  +
                </button>
              </div>

              <div
                className={`relative w-full origin-top-left will-change-transform ${
                  embeddedAr ? 'inline-block max-w-full' : 'inline-block max-w-full p-1'
                }`}
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                  transition: isPanning ? undefined : 'transform 160ms ease-out',
                }}
              >
                <img
                  src={displayImageUrl}
                  alt={
                    sideBySide
                      ? 'Историческое и современное фото с разметкой Archiview'
                      : 'Современное фото фасада с подсветкой Archiview'
                  }
                  width={imgSize.w}
                  height={imgSize.h}
                  draggable={false}
                  className={`block h-auto w-full select-none ${
                    embeddedAr
                      ? 'max-w-full rounded-none'
                      : 'max-h-[min(78vh,820px)] max-w-full rounded-xl'
                  }`}
                />
                {regions.length > 0 && (
                <svg
                  className="pointer-events-none absolute inset-0 h-full w-full overflow-visible"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                  aria-hidden
                >
                  {regions.map((r) => {
                    const on = hoverIdx === r.idx || selectedIdx === r.idx
                    const color = CLASS_COLORS[r.cls] ?? '#444'
                    const style = regionPolygonStyle(color, r.areaPct, on, variant === 'ar')
                    return (
                      <polygon
                        key={r.idx}
                        points={r.polygonPct.map(([x, y]) => `${x},${y}`).join(' ')}
                        fill={style.fill}
                        stroke={color}
                        strokeWidth={style.strokeWidth}
                      />
                    )
                  })}
                </svg>
              )}
              {regions.length > 0 && variant !== 'ar' && (
                <svg
                  className="pointer-events-none absolute inset-0 h-full w-full overflow-visible"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                  aria-hidden
                >
                  {regionsBadges.map((r) => {
                    if (!r.badgeLayout.callout) return null
                    const on = hoverIdx === r.idx || selectedIdx === r.idx
                    const color = CLASS_COLORS[r.cls] ?? '#444'
                    return (
                      <line
                        key={`callout-${r.idx}`}
                        x1={r.badgeLayout.anchorX}
                        y1={r.badgeLayout.anchorY}
                        x2={r.badgeLayout.badgeX}
                        y2={r.badgeLayout.badgeY}
                        stroke={color}
                        strokeWidth={on ? 0.42 : 0.32}
                        strokeOpacity={on ? 0.95 : 0.72}
                        vectorEffect="non-scaling-stroke"
                      />
                    )
                  })}
                </svg>
              )}
              {regions.length > 0 && variant !== 'ar' && (
                <div className="pointer-events-none absolute inset-0 z-20 overflow-visible" aria-hidden>
                  {regionsBadges.map((r) => {
                    const on = hoverIdx === r.idx || selectedIdx === r.idx
                    const color = CLASS_COLORS[r.cls] ?? '#444'
                    const size = on ? 26 : 22
                    const { badgeX, badgeY } = r.badgeLayout
                    return (
                      <div
                        key={`badge-${r.idx}`}
                        className="absolute z-20 flex items-center justify-center rounded-full border-2 border-white font-bold leading-none text-white shadow-md"
                        style={{
                          left: `${badgeX}%`,
                          top: `${badgeY}%`,
                          width: size,
                          height: size,
                          marginLeft: -size / 2,
                          marginTop: -size / 2,
                          backgroundColor: color,
                          fontSize: r.idx >= 10 ? 10 : 11,
                          boxShadow: '0 0 0 1px rgba(0,0,0,0.2)',
                        }}
                      >
                        {r.idx}
                      </div>
                    )
                  })}
                </div>
              )}
              {regions.length > 0 && (
                <svg
                  className="absolute inset-0 h-full w-full overflow-visible"
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
                  {selectedIdx !== null
                    ? (() => {
                        const r = regions.find((region) => region.idx === selectedIdx)
                        if (!r) return null
                        return (
                          <polygon
                            key={`hit-top-${r.idx}`}
                            points={r.polygonPct.map(([x, y]) => `${x},${y}`).join(' ')}
                            fill="transparent"
                            stroke="transparent"
                            className="cursor-pointer"
                            onMouseEnter={() => setHoverIdx(r.idx)}
                            onMouseLeave={() => setHoverIdx(null)}
                            onClick={() => setSelectedIdx(null)}
                          />
                        )
                      })()
                    : null}
                </svg>
              )}
              {plateRegion && platePlacement && variant !== 'ar' && !plateExpanded && (
                <div
                  className={`pointer-events-none absolute z-20 max-w-[min(92%,${
                    platePlacement.compact ? '260px' : '320px'
                  })] rounded-xl border border-arch-gold/70 bg-arch-green-deep/90 px-3 py-2.5 text-left text-xs leading-snug text-arch-surface shadow-xl backdrop-blur-md`}
                  style={{
                    left: `${plateRegion.cx}%`,
                    top: `${plateRegion.cy}%`,
                    transform: platePlacement.transform,
                  }}
                >
                  <ExpertTracePlate
                    idx={plateRegion.idx}
                    title={plateRegion.trace?.title ?? plateRegion.label}
                    period={plateRegion.trace?.period}
                    trace={plateRegion.trace}
                    comment={plateRegion.comment}
                    verification={building?.verification}
                    expanded={false}
                    compact={platePlacement.compact}
                  />
                </div>
              )}
              </div>

              {variant === 'ar' && plateRegion && !plateExpanded && (
                <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 border-t border-arch-surface/15 bg-arch-green-deep/92 px-3 py-2.5 backdrop-blur-sm">
                  <div className="flex items-center gap-2 text-xs text-arch-surface">
                    <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-arch-gold text-[10px] font-bold text-arch-green-deep">
                      {plateRegion.idx}
                    </span>
                    <span className="min-w-0 truncate font-medium">
                      {plateRegion.trace?.title ?? plateRegion.label}
                    </span>
                    {plateRegion.trace?.period ? (
                      <span className="hidden shrink-0 text-arch-surface/65 sm:inline">
                        {plateRegion.trace.period}
                      </span>
                    ) : null}
                  </div>
                </div>
              )}

              {plateExpanded && plateRegion && (
                <div
                  className={`absolute inset-0 z-40 flex items-center justify-center bg-black/55 ${
                    embeddedAr ? 'p-2' : 'p-4 sm:p-6'
                  }`}
                  role="dialog"
                  aria-modal="true"
                  aria-label={`Экспертная заметка ${plateRegion.idx}`}
                  onClick={() => setSelectedIdx(null)}
                >
                  <div
                    className={`pointer-events-auto max-h-[min(82%,520px)] w-full overflow-y-auto rounded-2xl border border-arch-gold/70 bg-arch-green-deep px-4 py-3.5 text-left text-xs leading-snug text-arch-surface shadow-2xl ${
                      embeddedAr ? 'max-w-none' : 'max-w-md'
                    }`}
                    onClick={(event) => event.stopPropagation()}
                  >
                    <ExpertTracePlate
                      idx={plateRegion.idx}
                      title={plateRegion.trace?.title ?? plateRegion.label}
                      period={plateRegion.trace?.period}
                      trace={plateRegion.trace}
                      comment={plateRegion.comment}
                      verification={building?.verification}
                      expanded
                      onClose={() => setSelectedIdx(null)}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {regions.length > 0 && !embeddedAr && (
            <ol
              className={`w-full shrink-0 space-y-1.5 text-sm ${
                variant === 'ar' ? '' : 'lg:w-64 xl:w-72'
              }`}
            >
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
                            {r.trace.period} · Экспертная заметка
                          </span>
                        ) : r.comment ? (
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
