import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type PointerEvent } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
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
import { FacadeBeforeAfterSlider } from './FacadeBeforeAfterSlider'
import { tracePlatePlacement, type BlockLayoutMetrics } from '../lib/tracePlatePlacement'
import {
  blockPctToViewportPct,
  loadPlateDragPositions,
  savePlateDragPositions,
  type PlateDragMap,
} from '../lib/tracePlateDragStorage'
import {
  TRACE_PLATE_SHELL_CLASS,
  TRACE_PLATE_SCROLL_CLASS,
  tracePlateBackground,
} from '../lib/tracePlateStyle'
import { computeBadgeLayout, assignBadgeLayouts, assignMobileBottomBadgeLayouts, type BadgeLayout } from '../lib/regionBadgeLayout'
import { useMediaQuery } from '../lib/useMediaQuery'

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
  mobileActive = false,
): { fill: string; strokeWidth: number } {
  if (mobileActive && on) {
    return {
      fill: `${color}66`,
      strokeWidth: 0.85,
    }
  }
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

/** Доля ширины фото — как BADGE_DIAMETER_PCT в regionBadgeLayout (2.6). */
const MOBILE_BADGE_WIDTH_RATIO = 0.0275
const MOBILE_BADGE_WIDTH_RATIO_ACTIVE = 0.0315

type FacadeBadgeMetrics = {
  size: number
  fontSize: number
  borderWidth: number
  ringWidth: number
}

function facadeBadgeMetrics(
  facadeImageWidth: number,
  active: boolean,
  twoDigit: boolean,
  scaleWithFacade: boolean,
): FacadeBadgeMetrics {
  if (!scaleWithFacade) {
    const size = active ? 26 : 22
    return {
      size,
      fontSize: twoDigit ? 11 : 12,
      borderWidth: 2,
      ringWidth: 2,
    }
  }
  const ratio = active ? MOBILE_BADGE_WIDTH_RATIO_ACTIVE : MOBILE_BADGE_WIDTH_RATIO
  const size = Math.max(14, Math.round(facadeImageWidth * ratio))
  return {
    size,
    fontSize: Math.max(8, Math.round(size * (twoDigit ? 0.36 : 0.4))),
    borderWidth: Math.max(1, Math.round(size * 0.09)),
    ringWidth: Math.max(1, Math.round(size * 0.08)),
  }
}

type Pan = { x: number; y: number }

function clampPct(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function blockLayoutsEqual(a: BlockLayoutMetrics | null, b: BlockLayoutMetrics | null): boolean {
  if (a === b) return true
  if (!a || !b) return false
  const eps = 0.2
  return (
    Math.abs(a.imageLeftPct - b.imageLeftPct) < eps &&
    Math.abs(a.imageTopPct - b.imageTopPct) < eps &&
    Math.abs(a.imageWidthPct - b.imageWidthPct) < eps &&
    Math.abs(a.imageHeightPct - b.imageHeightPct) < eps
  )
}

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
  },
): Promise<{ url: string; kind: FacadeImageKind; w: number; h: number } | null> {
  if (options?.arMode) {
    /** Полевой кадр — только если в facade-project.json есть H_rect_to_ar. */
    if (options.hasArHomography && assets.arPhotoUrl) {
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

    if (assets.arPhotoUrl) {
      const arPhoto = await probeImageMeta(assets.arPhotoUrl)
      if (arPhoto) {
        return { url: assets.arPhotoUrl, kind: 'source_modern', w: arPhoto.w, h: arPhoto.h }
      }
    }

    /** Запасной вариант, пока modern-source.png не экспортирован из Archiview (напр. MOSCOW_001). */
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
  mobileArPlateHost = null,
}: {
  assets: ArchiviewBuildingAssets
  building?: Building
  variant?: 'default' | 'ar'
  /** Внутри рамки телефона в AR-симуляции */
  embeddedAr?: boolean
  /** Скрыть подпись (её рисует FacadeARPreview внутри экрана) */
  hideIntro?: boolean
  /** На телефоне: контейнер под экраном AR для развёрнутой карточки следа */
  mobileArPlateHost?: HTMLDivElement | null
}) {
  const [regions, setRegions] = useState<DisplayRegion[]>([])
  const [imageOk, setImageOk] = useState(false)
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)
  const hoverClearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const setHoverRegion = useCallback((idx: number | null) => {
    if (hoverClearTimerRef.current) {
      clearTimeout(hoverClearTimerRef.current)
      hoverClearTimerRef.current = null
    }
    if (idx !== null) {
      setHoverIdx(idx)
      return
    }
    hoverClearTimerRef.current = setTimeout(() => setHoverIdx(null), 140)
  }, [])

  useEffect(
    () => () => {
      if (hoverClearTimerRef.current) clearTimeout(hoverClearTimerRef.current)
    },
    [],
  )
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null)
  const isMobile = useMediaQuery('(max-width: 639px)')
  const embeddedArMobileBelow = embeddedAr && isMobile
  const [internalBelowPhotoHost, setInternalBelowPhotoHost] = useState<HTMLDivElement | null>(null)
  const belowPhotoPlateHost = mobileArPlateHost ?? internalBelowPhotoHost
  const useMobileFacadeChrome = isMobile && !embeddedAr && variant !== 'ar'
  const useMobileNearRegionBadges =
    useMobileFacadeChrome &&
    ((assets.cardId === 'MOSCOW_001' && assets.comparisonId === 'cmp_005') ||
      assets.cardId === 'MOSCOW_003' ||
      assets.cardId === 'MOSCOW_004')
  const useMobileBottomBadges =
    useMobileFacadeChrome &&
    !useMobileNearRegionBadges &&
    assets.comparisonId !== 'cmp_009' &&
    assets.comparisonId !== 'cmp_008'
  const mobileBadgeClicks = isMobile && !embeddedAr && variant !== 'ar'
  const [imgSize, setImgSize] = useState({ w: 1, h: 1 })
  const [sideBySide, setSideBySide] = useState(false)
  const [displayImageUrl, setDisplayImageUrl] = useState('')
  const [imageKind, setImageKind] = useState<FacadeImageKind | null>(null)
  const [zoom, setZoom] = useState(ZOOM_MIN)
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const viewportRef = useRef<HTMLDivElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const facadeBlockRef = useRef<HTMLDivElement>(null)
  const [blockLayout, setBlockLayout] = useState<BlockLayoutMetrics | null>(null)
  const [facadeImageWidth, setFacadeImageWidth] = useState(0)
  const [plateDragPositions, setPlateDragPositions] = useState<PlateDragMap>({})
  const [isPlateDragging, setIsPlateDragging] = useState(false)
  const plateDragSessionRef = useRef<{
    pointerId: number
    regionIdx: number
    startX: number
    startY: number
    startLeftPct: number
    startTopPct: number
    moved: boolean
  } | null>(null)
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
    (event: PointerEvent<HTMLDivElement>) => {
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
        badgeLayout: computeBadgeLayout(
          polygonPct,
          areaPct,
          idx,
          assets.cardId,
          assets.comparisonId,
        ),
      }
    },
    [assets.cardId, assets.comparisonId, tracesById],
  )

  const publishRegions = useCallback(
    (list: DisplayRegion[]) => {
      if (useMobileBottomBadges) {
        assignMobileBottomBadgeLayouts(list)
      } else {
        assignBadgeLayouts(list, assets.cardId, assets.comparisonId, {
          mobile: useMobileNearRegionBadges,
        })
      }
      setRegions(list)
    },
    [assets.cardId, assets.comparisonId, useMobileBottomBadges, useMobileNearRegionBadges],
  )

  useEffect(() => {
    if (regions.length === 0) return
    setRegions((prev) => {
      const next = prev.map((region) => ({ ...region }))
      if (useMobileBottomBadges) {
        assignMobileBottomBadgeLayouts(next)
      } else {
        assignBadgeLayouts(next, assets.cardId, assets.comparisonId, {
          mobile: useMobileNearRegionBadges,
        })
      }
      return next
    })
  }, [useMobileBottomBadges, useMobileNearRegionBadges, assets.cardId, assets.comparisonId, regions.length])

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

      const loaded = await pickFacadeImage(assets, {
        arMode: variant === 'ar',
        hasArHomography: Boolean(H_ar),
        preferRectified: variant === 'default' && !isSb,
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
      const useSourcePolygonsAr =
        variant === 'ar' &&
        !isArFieldPhoto &&
        loaded.kind === 'source_modern' &&
        annotationsHaveSourcePolygons(annotations)
      const useSourcePolygons =
        !isSb &&
        loaded.kind === 'source_modern' &&
        !useArHomography &&
        !useFieldHomography &&
        !useSourcePolygonsOnField &&
        !useSourcePolygonsAr &&
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
      } else if (useSourcePolygonsOnField || useSourcePolygonsAr || useSourcePolygons) {
        buildRegionsFromSourcePolygons(annotations, loaded.w, loaded.h, sourcePolygonOffset)
      } else if (useArHomography || useFieldHomography) {
        buildRegionsOverlay(annotations, H!, loaded.w, loaded.h)
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

  /** Overlay на карточке: слева фасад + слайдер, справа список следов сверху. */
  const useSidebarLayout = !embeddedAr && !sideBySide && variant === 'default'

  const platePlacement = useMemo(() => {
    if (!plateRegion) return null
    const xs = plateRegion.polygonPct.map((p) => p[0])
    const ys = plateRegion.polygonPct.map((p) => p[1])
    return tracePlatePlacement(plateRegion.cx, plateRegion.cy, plateExpanded, {
      bbox: {
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
      },
      layout: blockLayout ?? undefined,
      sidebarLayout: useSidebarLayout,
      cardId: assets.cardId,
      regionIdx: plateRegion.idx,
      avoidRegionOverlap: embeddedAr && !plateExpanded,
    })
  }, [plateRegion, plateExpanded, blockLayout, useSidebarLayout, assets.cardId, embeddedAr])

  useEffect(() => {
    if (!assets.cardId) {
      setPlateDragPositions({})
      return
    }
    setPlateDragPositions(loadPlateDragPositions(assets.cardId))
  }, [assets.cardId])

  const resetPlateDragPosition = useCallback(
    (regionIdx: number) => {
      if (!assets.cardId) return
      setPlateDragPositions((prev) => {
        if (!prev[regionIdx]) return prev
        const next = { ...prev }
        delete next[regionIdx]
        savePlateDragPositions(assets.cardId, next)
        return next
      })
    },
    [assets.cardId],
  )

  const [plateAutoViewport, setPlateAutoViewport] = useState<{ xPct: number; yPct: number } | null>(
    null,
  )

  const PLATE_POS_EPS = 0.5
  const blockLayoutRafRef = useRef<number | null>(null)

  useLayoutEffect(() => {
    if (!plateRegion || !platePlacement) {
      setPlateAutoViewport(null)
      return
    }
    if (plateDragPositions[plateRegion.idx]) {
      setPlateAutoViewport(null)
      return
    }
    const block = facadeBlockRef.current
    if (!block) return
    const blockRect = block.getBoundingClientRect()
    if (blockRect.width < 1 || blockRect.height < 1) return
    const next = blockPctToViewportPct(platePlacement.leftPct, platePlacement.topPct, blockRect)
    setPlateAutoViewport((prev) => {
      if (
        prev &&
        Math.abs(prev.xPct - next.xPct) < PLATE_POS_EPS &&
        Math.abs(prev.yPct - next.yPct) < PLATE_POS_EPS
      ) {
        return prev
      }
      return next
    })
  }, [plateDragPositions, platePlacement, plateRegion, blockLayout, zoom, pan.x, pan.y])

  const plateViewportPosition = useMemo(() => {
    if (!plateRegion || !platePlacement) return null
    const saved = plateDragPositions[plateRegion.idx]
    if (saved) {
      return { xPct: saved.xPct, yPct: saved.yPct, isCustom: true }
    }
    if (plateAutoViewport) {
      return { ...plateAutoViewport, isCustom: false }
    }
    return null
  }, [plateAutoViewport, plateDragPositions, platePlacement, plateRegion])

  useLayoutEffect(() => {
    if (!embeddedAr || !imageOk) return
    const vp = viewportRef.current
    if (!vp) return
    vp.scrollTop = 0
    vp.scrollLeft = 0
  }, [embeddedAr, imageOk, displayImageUrl, imgSize.w, imgSize.h, regions.length])

  const resetArViewportScroll = useCallback(() => {
    if (!embeddedAr) return
    const vp = viewportRef.current
    if (!vp) return
    vp.scrollTop = 0
    vp.scrollLeft = 0
  }, [embeddedAr])

  const handlePlateDragStart = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      if (!plateRegion || !platePlacement || !plateViewportPosition) return
      if (event.button !== 0) return
      event.preventDefault()
      event.stopPropagation()

      plateDragSessionRef.current = {
        pointerId: event.pointerId,
        regionIdx: plateRegion.idx,
        startX: event.clientX,
        startY: event.clientY,
        startLeftPct: plateViewportPosition.xPct,
        startTopPct: plateViewportPosition.yPct,
        moved: false,
      }
      setIsPlateDragging(true)
      event.currentTarget.setPointerCapture(event.pointerId)
    },
    [platePlacement, plateRegion, plateViewportPosition],
  )

  const handlePlateDragMove = useCallback((event: PointerEvent<HTMLDivElement>) => {
    const session = plateDragSessionRef.current
    if (!session || session.pointerId !== event.pointerId) return

    const dxPct = ((event.clientX - session.startX) / window.innerWidth) * 100
    const dyPct = ((event.clientY - session.startY) / window.innerHeight) * 100
    if (Math.abs(dxPct) > 0.1 || Math.abs(dyPct) > 0.1) session.moved = true

    const nextPos = {
      xPct: clampPct(session.startLeftPct + dxPct, 2, 98),
      yPct: clampPct(session.startTopPct + dyPct, 2, 98),
    }

    setPlateDragPositions((prev) => ({
      ...prev,
      [session.regionIdx]: nextPos,
    }))
  }, [])

  const handlePlateDragEnd = useCallback(
    (event: PointerEvent<HTMLDivElement>) => {
      const session = plateDragSessionRef.current
      if (!session || session.pointerId !== event.pointerId) return

      if (session.moved && assets.cardId) {
        setPlateDragPositions((prev) => {
          const pos = prev[session.regionIdx]
          if (pos) savePlateDragPositions(assets.cardId, prev)
          return prev
        })
      }

      plateDragSessionRef.current = null
      setIsPlateDragging(false)
      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId)
      }
    },
    [assets.cardId],
  )

  useLayoutEffect(() => {
    const measureBlockLayout = () => {
      const block = facadeBlockRef.current
      const viewport = viewportRef.current
      if (!block || !viewport) {
        setBlockLayout((prev) => (prev === null ? prev : null))
        return
      }
      const blockRect = block.getBoundingClientRect()
      const vpRect = viewport.getBoundingClientRect()
      if (blockRect.width < 1 || blockRect.height < 1) return
      const next: BlockLayoutMetrics = {
        imageLeftPct: ((vpRect.left - blockRect.left) / blockRect.width) * 100,
        imageTopPct: ((vpRect.top - blockRect.top) / blockRect.height) * 100,
        imageWidthPct: (vpRect.width / blockRect.width) * 100,
        imageHeightPct: (vpRect.height / blockRect.height) * 100,
      }
      setBlockLayout((prev) => (blockLayoutsEqual(prev, next) ? prev : next))
    }

    const updateBlockLayout = () => {
      if (blockLayoutRafRef.current !== null) return
      blockLayoutRafRef.current = requestAnimationFrame(() => {
        blockLayoutRafRef.current = null
        measureBlockLayout()
      })
    }

    measureBlockLayout()
    const ro = new ResizeObserver(updateBlockLayout)
    const block = facadeBlockRef.current
    const viewport = viewportRef.current
    if (block) ro.observe(block)
    if (viewport) ro.observe(viewport)
    window.addEventListener('resize', updateBlockLayout)
    window.addEventListener('scroll', updateBlockLayout, { capture: true, passive: true })
    return () => {
      if (blockLayoutRafRef.current !== null) {
        cancelAnimationFrame(blockLayoutRafRef.current)
        blockLayoutRafRef.current = null
      }
      ro.disconnect()
      window.removeEventListener('resize', updateBlockLayout)
      window.removeEventListener('scroll', updateBlockLayout, true)
    }
  }, [zoom, pan.x, pan.y, imgSize.w, imgSize.h, displayImageUrl, regions.length, useSidebarLayout])

  useLayoutEffect(() => {
    const img = imageRef.current
    if (!img) {
      setFacadeImageWidth(0)
      return
    }
    const update = () => {
      const width = img.getBoundingClientRect().width
      setFacadeImageWidth((prev) => (Math.abs(prev - width) < 0.5 ? prev : width))
    }
    update()
    const ro = new ResizeObserver(update)
    ro.observe(img)
    return () => ro.disconnect()
  }, [displayImageUrl, imgSize.w, imgSize.h, zoom, pan.x, pan.y, sideBySide, imageOk])

  /** Small regions (e.g. #6, #9) must paint above large overlaps (#12) for clicks — render largest first, smallest last in SVG. */
  const regionsForHit = useMemo(
    () => [...regions].sort((a, b) => polygonAreaAbs(b.polygonPct) - polygonAreaAbs(a.polygonPct)),
    [regions],
  )

  const regionsBadges = useMemo(
    () => [...regions].sort((a, b) => polygonAreaAbs(b.polygonPct) - polygonAreaAbs(a.polygonPct)),
    [regions],
  )

  const scaleBadgesWithFacade = mobileBadgeClicks

  const tracePlateContent = plateRegion ? (
    <ExpertTracePlate
      idx={plateRegion.idx}
      title={plateRegion.trace?.title ?? plateRegion.label}
      period={plateRegion.trace?.period}
      trace={plateRegion.trace}
      comment={plateRegion.comment}
      verification={building?.verification}
      expanded={plateExpanded}
      compact={embeddedAr ? !plateExpanded : Boolean(platePlacement?.compact)}
      onClose={plateExpanded ? () => setSelectedIdx(null) : undefined}
    />
  ) : null

  const embeddedPlateLayout = useMemo(() => {
    if (!embeddedAr || !plateRegion || plateExpanded) return null
    if (isMobile) {
      return {
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        maxWidth: 'calc(100% - 1rem)',
      }
    }
    if (!platePlacement) return null
    return {
      left: `${platePlacement.leftPct}%`,
      top: `${platePlacement.topPct}%`,
      transform: platePlacement.transform,
      maxWidth: `min(92%, ${Math.max(platePlacement.maxWidthPx, 220)}px)`,
    }
  }, [embeddedAr, isMobile, plateExpanded, platePlacement, plateRegion])

  const showEmbeddedMobileBelowPlate = Boolean(
    embeddedArMobileBelow &&
      plateExpanded &&
      plateRegion &&
      tracePlateContent &&
      belowPhotoPlateHost,
  )

  const showArDesktopExpandedPortal = Boolean(
    embeddedAr && !isMobile && plateExpanded && plateRegion && tracePlateContent,
  )

  const showMobilePortal =
    isMobile &&
    Boolean(plateRegion && platePlacement && tracePlateContent) &&
    (!embeddedAr || plateExpanded) &&
    !showEmbeddedMobileBelowPlate

  const platePortalStyle = useMemo(() => {
    if (showArDesktopExpandedPortal) {
      return {
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)' as const,
        maxWidth: 'min(440px, calc(100vw - 1.5rem))',
        minWidth: 'min(300px, calc(100vw - 1.5rem))',
        width: 'min(440px, calc(100vw - 1.5rem))' as const,
        backgroundColor: tracePlateBackground(true),
      }
    }
    if (!platePlacement) return null
    const shared = {
      transform: 'translate(-50%, -50%)' as const,
      maxWidth: plateExpanded
        ? 'min(440px, calc(100vw - 1.5rem))'
        : `min(${Math.max(platePlacement.maxWidthPx, 300)}px, calc(100vw - 1.5rem))`,
      minWidth: plateExpanded ? 'min(300px, calc(100vw - 1.5rem))' : 'min(240px, calc(100vw - 1.5rem))',
      width: plateExpanded ? ('min(440px, calc(100vw - 1.5rem))' as const) : undefined,
      backgroundColor: tracePlateBackground(plateExpanded),
    }
    if (isMobile) {
      return {
        left: '50%',
        top: '50%',
        ...shared,
      }
    }
    if (!plateViewportPosition) return null
    return {
      left: `${plateViewportPosition.xPct}vw`,
      top: `${plateViewportPosition.yPct}vh`,
      ...shared,
    }
  }, [isMobile, plateExpanded, platePlacement, plateViewportPosition, showArDesktopExpandedPortal])

  const showDesktopPortal =
    !isMobile &&
    !embeddedAr &&
    Boolean(plateRegion && platePlacement && plateViewportPosition && tracePlateContent) &&
    !(variant === 'ar' && plateExpanded)

  const showPlatePortal = showMobilePortal || showDesktopPortal || showArDesktopExpandedPortal

  const comparisonBlock =
    !sideBySide && variant === 'default' ? (
      <div className="min-w-0">
        <h3 className="mb-2 text-base font-semibold text-arch-green-deep">
          Сравнение фотоматериалов
          {assets.historicalPhotoYear && assets.modernPhotoYear
            ? ` (${assets.historicalPhotoYear} → ${assets.modernPhotoYear})`
            : ''}
        </h3>
        <FacadeBeforeAfterSlider
          historicalUrl={assets.historicalRectifiedUrl}
          modernUrl={assets.modernRectifiedUrl}
          historicalYear={assets.historicalPhotoYear}
          modernYear={assets.modernPhotoYear}
        />
      </div>
    ) : null

  const regionList =
    regions.length > 0 ? (
      <ol
        className={`w-full text-sm ${
          sideBySide ? 'grid grid-cols-1 gap-2 sm:grid-cols-3' : 'space-y-1.5'
        }`}
      >
        {regions.map((r) => {
          const on = hoverIdx === r.idx
          const color = CLASS_COLORS[r.cls] ?? '#444'
          return (
            <li key={r.idx} className={sideBySide ? 'min-w-0' : undefined}>
              <button
                type="button"
                onMouseEnter={() => setHoverRegion(r.idx)}
                onMouseLeave={() => setHoverRegion(null)}
                onFocus={() => setHoverRegion(r.idx)}
                onBlur={() => setHoverRegion(null)}
                onClick={() => setSelectedIdx((current) => (current === r.idx ? null : r.idx))}
                className={`flex gap-2 rounded-lg border px-2.5 py-2 text-left transition ${
                  sideBySide ? 'h-full min-h-[5.5rem] flex-col items-start' : 'w-full'
                } ${
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
                  <span
                    className={`block font-medium leading-tight text-arch-ink ${
                      sideBySide ? 'line-clamp-2 text-[13px]' : ''
                    }`}
                  >
                    {r.trace?.title ?? r.label}
                  </span>
                  {r.trace ? (
                    <span
                      className={`mt-0.5 block text-arch-muted ${
                        sideBySide ? 'line-clamp-2 text-[11px]' : 'text-xs'
                      }`}
                    >
                      {r.trace.period}
                    </span>
                  ) : r.comment ? (
                    <span
                      className={`mt-0.5 block text-arch-muted ${
                        sideBySide ? 'line-clamp-3 text-[11px]' : 'text-xs'
                      }`}
                    >
                      {r.comment}
                    </span>
                  ) : null}
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    ) : null

  return (
    <div className={embeddedAr ? (embeddedArMobileBelow ? 'space-y-0' : 'h-full space-y-0') : 'space-y-3'}>
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
              Выпрямленное фото с подсветкой областей. Номера и цветные зоны на фото; список следов —
              справа. При наведении — краткая плашка, <strong>клик</strong> по зоне или заметке в списке —
              полная карточка с источниками и достоверностью. Плашку можно{' '}
              <strong>перетащить</strong> за верхнюю полоску — позиция запомнится в браузере. Ниже —
              сравнение архив / современность.
              Кнопки <strong>+</strong> / <strong>−</strong> приближают фото; при увеличении можно
              сдвигать картинку мышью.
            </>
          ) : (
            <>
              Современное фото в исходном ракурсе с подсветкой областей. Номера и цветные зоны видны
              сразу; при наведении — краткая плашка, <strong>клик</strong> по зоне или заметке в списке —
              полная карточка с источниками и достоверностью. Плашку можно{' '}
              <strong>перетащить</strong> за верхнюю полоску — позиция запомнится в браузере. Кнопки{' '}
              <strong>+</strong> / <strong>−</strong>{' '}
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
              Для AR-preview нужно исходное фото <code>modern-source.png</code> (файл{' '}
              <code>11_modern_source_for_site.png</code> из Archiview). Экспортируйте через{' '}
              <code>copy_to_website.bat</code> (CardId: {assets.cardId}) → Push → Ctrl+F5.
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
        <div
          ref={facadeBlockRef}
          className={`relative ${
            embeddedAr
              ? embeddedArMobileBelow
                ? 'overflow-visible'
                : 'h-full min-h-0 overflow-hidden'
              : 'overflow-visible'
          }`}
        >
          <div
            className={
              useSidebarLayout
                ? isMobile
                  ? 'flex flex-col gap-4 lg:grid lg:grid-cols-[minmax(0,1fr)_17rem] lg:grid-rows-[auto_auto] xl:grid-cols-[minmax(0,1fr)_20rem] lg:items-start'
                  : 'grid grid-cols-1 gap-4 md:grid-cols-[minmax(0,1fr)_17rem] xl:grid-cols-[minmax(0,1fr)_20rem] md:items-start'
                : embeddedAr
                  ? embeddedArMobileBelow
                    ? 'flex w-full flex-col'
                    : 'flex h-full min-h-0 flex-col'
                  : 'flex flex-col gap-4'
            }
          >
          <div
            className={
              useSidebarLayout
                ? isMobile
                  ? 'relative order-1 flex min-w-0 flex-col gap-4 overflow-visible lg:col-start-1 lg:row-start-1'
                  : 'relative order-1 flex min-w-0 flex-col gap-4 overflow-visible md:col-start-1 md:row-start-1 md:row-span-2'
                : embeddedAr
                  ? embeddedArMobileBelow
                    ? 'relative flex w-full min-w-0 flex-col'
                    : 'relative flex h-full min-h-0 min-w-0 w-full flex-col'
                  : 'relative min-w-0 w-full overflow-visible'
            }
          >
          <div className={embeddedAr && !embeddedArMobileBelow ? 'relative min-h-0 min-w-0 flex-1' : 'relative min-w-0 shrink-0 w-full'}>
            <div
              ref={viewportRef}
              className={`relative w-full ${
                embeddedAr ? '' : 'shadow-sm'
              } ${
                variant === 'ar'
                  ? embeddedAr
                    ? embeddedArMobileBelow
                      ? 'bg-arch-green-deep'
                      : 'h-full bg-arch-green-deep'
                    : 'rounded-lg border border-arch-surface/15 bg-arch-green-deep/80'
                  : 'rounded-xl border border-arch-line bg-arch-surface-2/20'
              } ${
                zoom > ZOOM_MIN
                  ? embeddedAr
                    ? embeddedArMobileBelow
                      ? 'overflow-hidden'
                      : 'h-full max-h-none overflow-hidden'
                    : 'max-h-[min(78vh,820px)] overflow-hidden'
                  : embeddedAr
                    ? embeddedArMobileBelow
                      ? 'overflow-hidden'
                      : 'h-full overflow-x-hidden overflow-y-auto [overflow-anchor:none]'
                    : 'overflow-hidden'
              } ${zoom > ZOOM_MIN ? (isPanning ? 'cursor-grabbing' : 'cursor-grab') : ''}`}
              onMouseLeave={() => setHoverRegion(null)}
              onPointerDown={handleViewportPointerDown}
              onPointerMove={handleViewportPointerMove}
              onPointerUp={endPanSession}
              onPointerCancel={endPanSession}
            >
              {plateExpanded && variant !== 'ar' ? (
                <button
                  type="button"
                  className="absolute inset-0 z-30 cursor-default border-0 bg-transparent p-0"
                  aria-label="Закрыть карточку"
                  onClick={() => setSelectedIdx(null)}
                />
              ) : null}
              {plateExpanded && variant === 'ar' ? (
                <button
                  type="button"
                  className="absolute inset-0 z-40 cursor-default border-0 bg-transparent p-0"
                  aria-label="Закрыть карточку"
                  onClick={() => setSelectedIdx(null)}
                />
              ) : null}
              {!embeddedAr ? (
              <div
                className="absolute right-2 top-2 z-40 flex items-center gap-1 rounded-lg border border-arch-line/80 bg-arch-surface/95 p-1 shadow-md backdrop-blur-sm"
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
              ) : null}

              {variant === 'ar' && imageKind === 'rectified' && !(embeddedAr && isMobile) ? (
                <div className="pointer-events-none absolute inset-x-0 top-0 z-30 border-b border-amber-400/40 bg-amber-950/75 px-3 py-1.5 text-center text-[11px] leading-snug text-amber-100/95">
                  Исходное фото ещё не на сайте — показано выпрямленное. Экспортируйте{' '}
                  <code className="text-amber-50">modern-source.png</code> из Archiview.
                </div>
              ) : null}

              <div
                className={`relative origin-top-left will-change-transform ${
                  embeddedAr ? 'block w-full' : 'mx-auto inline-block max-w-full p-1'
                }`}
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                  transition: isPanning ? undefined : 'transform 160ms ease-out',
                }}
              >
                <img
                  ref={imageRef}
                  src={displayImageUrl}
                  alt={
                    sideBySide
                      ? 'Историческое и современное фото с разметкой Archiview'
                      : 'Современное фото фасада с подсветкой Archiview'
                  }
                  width={imgSize.w}
                  height={imgSize.h}
                  draggable={false}
                  onLoad={resetArViewportScroll}
                  className={`block w-full select-none ${
                    embeddedAr
                      ? 'h-auto max-w-full rounded-none'
                      : 'h-auto w-auto max-w-full max-h-[min(78vh,820px)] rounded-xl'
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
                    const style = regionPolygonStyle(color, r.areaPct, on, variant === 'ar', useMobileFacadeChrome)
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
              {regions.length > 0 && (
                <svg
                  className="absolute inset-0 z-10 h-full w-full touch-manipulation overflow-visible"
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
                      onMouseEnter={() => setHoverRegion(r.idx)}
                      onMouseLeave={() => setHoverRegion(null)}
                      onFocus={() => setHoverRegion(r.idx)}
                      onBlur={() => setHoverRegion(null)}
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
                            onMouseEnter={() => setHoverRegion(r.idx)}
                            onMouseLeave={() => setHoverRegion(null)}
                            onClick={() => setSelectedIdx(null)}
                          />
                        )
                      })()
                    : null}
                </svg>
              )}
              {regions.length > 0 && variant !== 'ar' ? (
                <div
                  className={`absolute inset-0 z-20 overflow-visible ${useMobileFacadeChrome ? '' : 'pointer-events-none'}`}
                  aria-hidden={!useMobileFacadeChrome}
                >
                  <svg
                    className="absolute inset-0 h-full w-full overflow-visible"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                  >
                    {regionsBadges.map((r) => {
                      if (!useMobileBottomBadges && !r.badgeLayout.callout) return null
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
                          strokeWidth={on ? 0.48 : 0.34}
                          strokeOpacity={on ? 0.98 : 0.75}
                        />
                      )
                    })}
                  </svg>
                  {regionsBadges.map((r) => {
                    const on = hoverIdx === r.idx || selectedIdx === r.idx
                    const color = CLASS_COLORS[r.cls] ?? '#444'
                    const badge = facadeBadgeMetrics(
                      facadeImageWidth || 320,
                      on,
                      r.idx >= 10,
                      scaleBadgesWithFacade,
                    )
                    const { badgeX, badgeY } = r.badgeLayout
                    return (
                      <button
                        key={`badge-${r.idx}`}
                        type="button"
                        aria-label={`Зона ${r.idx}`}
                        onMouseEnter={() => setHoverRegion(r.idx)}
                        onMouseLeave={() => setHoverRegion(null)}
                        onFocus={() => setHoverRegion(r.idx)}
                        onBlur={() => setHoverRegion(null)}
                        onClick={(event) => {
                          event.stopPropagation()
                          setSelectedIdx((current) => (current === r.idx ? null : r.idx))
                        }}
                        className={`absolute flex items-center justify-center rounded-full border-solid font-bold leading-none text-white shadow-md ${
                          mobileBadgeClicks ? 'pointer-events-auto cursor-pointer' : 'pointer-events-none'
                        } border-white`}
                        style={{
                          left: `${badgeX}%`,
                          top: `${badgeY}%`,
                          width: badge.size,
                          height: badge.size,
                          marginLeft: -badge.size / 2,
                          marginTop: -badge.size / 2,
                          backgroundColor: color,
                          fontSize: badge.fontSize,
                          borderWidth: badge.borderWidth,
                          boxShadow: on
                            ? `0 0 0 ${badge.ringWidth}px rgba(255,255,255,0.9), 0 0 0 ${badge.ringWidth + badge.borderWidth}px ${color}88, 0 ${Math.max(1, Math.round(badge.size * 0.08))}px ${Math.max(2, Math.round(badge.size * 0.22))}px rgba(0,0,0,0.35)`
                            : `0 0 0 ${Math.max(1, Math.round(badge.borderWidth * 0.5))}px rgba(0,0,0,0.2)`,
                        }}
                      >
                        {r.idx}
                      </button>
                    )
                  })}
                </div>
              ) : null}
              {embeddedAr && plateRegion && tracePlateContent && embeddedPlateLayout ? (
                <div
                  className={`absolute z-50 ${TRACE_PLATE_SHELL_CLASS} overflow-hidden shadow-2xl backdrop-blur-xl pointer-events-none`}
                  style={{
                    left: embeddedPlateLayout.left,
                    top: embeddedPlateLayout.top,
                    transform: embeddedPlateLayout.transform,
                    maxWidth: embeddedPlateLayout.maxWidth,
                    backgroundColor: tracePlateBackground(false),
                  }}
                  aria-label={`Экспертная заметка ${plateRegion.idx}`}
                >
                  <div className="px-3 py-2 text-sm leading-snug">{tracePlateContent}</div>
                </div>
              ) : null}
              </div>

            </div>
            {embeddedArMobileBelow ? (
              <div
                ref={setInternalBelowPhotoHost}
                className="shrink-0 border-t border-arch-surface/10 bg-arch-green-deep px-3 py-2 empty:hidden"
              />
            ) : null}
            {sideBySide && regionList ? (
              <div className="w-full pt-2">{regionList}</div>
            ) : null}

            {useSidebarLayout && !isMobile && comparisonBlock ? (
              <div className="relative z-0 min-w-0">{comparisonBlock}</div>
            ) : null}
          </div>
          </div>

          {useSidebarLayout && isMobile && regionList ? (
            <div className="relative z-0 order-2 flex min-w-0 flex-col lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:min-h-[min(78vh,820px)] lg:self-stretch">
              {regionList}
              {building && !sideBySide ? (
                <Link
                  to={`/building/${building.id}/ar`}
                  className="mt-4 inline-flex items-center justify-center gap-1 rounded-full border border-arch-line bg-arch-surface px-4 py-2.5 text-sm font-medium text-arch-green-deep transition hover:border-arch-green/40 hover:bg-arch-green-soft"
                >
                  AR-preview: подсветка на полевом фото →
                </Link>
              ) : null}
            </div>
          ) : null}

          {useSidebarLayout && isMobile && comparisonBlock ? (
            <div className="relative z-0 order-3 min-w-0 lg:col-start-1 lg:row-start-2">{comparisonBlock}</div>
          ) : null}

          {useSidebarLayout && !isMobile && regionList ? (
            <div className="relative z-0 order-2 flex min-w-0 flex-col md:col-start-2 md:row-start-1 md:row-span-2 md:min-h-[min(78vh,820px)] md:self-stretch">
              {regionList}
              {building && !sideBySide ? (
                <Link
                  to={`/building/${building.id}/ar`}
                  className="mt-4 inline-flex items-center justify-center gap-1 rounded-full border border-arch-line bg-arch-surface px-4 py-2.5 text-sm font-medium text-arch-green-deep transition hover:border-arch-green/40 hover:bg-arch-green-soft"
                >
                  AR-preview: подсветка на полевом фото →
                </Link>
              ) : null}
            </div>
          ) : null}
          </div>

          {!useSidebarLayout && !embeddedAr && !sideBySide && (regionList || comparisonBlock) ? (
            <div className={`flex flex-col gap-4 ${isMobile ? '' : 'lg:flex-row lg:items-start'}`}>
              {isMobile ? (
                <>
                  {regionList ? <div className="flex w-full shrink-0 flex-col">{regionList}</div> : null}
                  {comparisonBlock}
                </>
              ) : (
                <>
                  {comparisonBlock}
                  {regionList ? (
                    <div className="flex w-full shrink-0 flex-col lg:w-72 xl:w-80">
                      {regionList}
                    </div>
                  ) : null}
                </>
              )}
              {building && !sideBySide ? (
                <Link
                  to={`/building/${building.id}/ar`}
                  className="inline-flex items-center justify-center gap-1 rounded-full border border-arch-line bg-arch-surface px-4 py-2.5 text-sm font-medium text-arch-green-deep transition hover:border-arch-green/40 hover:bg-arch-green-soft"
                >
                  AR-preview: подсветка на полевом фото →
                </Link>
              ) : null}
            </div>
          ) : null}

        </div>
      )}
      {showEmbeddedMobileBelowPlate && belowPhotoPlateHost
        ? createPortal(
            <div
              className={`${TRACE_PLATE_SHELL_CLASS} pointer-events-auto overflow-hidden shadow-2xl backdrop-blur-xl`}
              style={{ backgroundColor: tracePlateBackground(true) }}
              role="dialog"
              aria-modal="true"
              aria-label={`Экспертная заметка ${plateRegion!.idx}`}
            >
              <div className={`max-h-[min(38vh,260px)] overflow-y-auto px-4 py-3 ${TRACE_PLATE_SCROLL_CLASS}`}>{tracePlateContent}</div>
            </div>,
            belowPhotoPlateHost,
          )
        : null}
      {showPlatePortal && platePortalStyle
        ? createPortal(
            <>
              {plateExpanded && (isMobile || showArDesktopExpandedPortal) ? (
                <button
                  type="button"
                  className="fixed inset-0 z-[9989] border-0 bg-arch-ink/45 p-0"
                  aria-label="Закрыть карточку"
                  onClick={() => setSelectedIdx(null)}
                />
              ) : null}
              <div
                className={`fixed z-[9990] ${TRACE_PLATE_SHELL_CLASS} ${
                  plateExpanded ? 'pointer-events-auto' : 'pointer-events-none'
                } ${plateExpanded ? '' : 'rounded-lg shadow-xl'} ${isPlateDragging ? 'select-none' : ''}`}
                style={platePortalStyle}
                role={plateExpanded ? 'dialog' : undefined}
                aria-modal={plateExpanded ? true : undefined}
                aria-label={plateExpanded ? `Экспертная заметка ${plateRegion!.idx}` : undefined}
                onClick={plateExpanded ? (event) => event.stopPropagation() : undefined}
              >
                {plateExpanded && !embeddedAr && !isMobile ? (
                  <div
                    className={`flex touch-none items-center gap-2 border-b border-arch-gold/35 bg-arch-green-deep/20 px-2.5 py-1.5 ${
                      isPlateDragging ? 'cursor-grabbing' : 'cursor-grab'
                    }`}
                    aria-label="Перетащить карточку"
                    onPointerDown={handlePlateDragStart}
                    onPointerMove={handlePlateDragMove}
                    onPointerUp={handlePlateDragEnd}
                    onPointerCancel={handlePlateDragEnd}
                  >
                    <span className="text-xs tracking-widest text-arch-surface/45" aria-hidden>
                      ⋮⋮
                    </span>
                    <span className="text-[10px] text-arch-surface/55">перетащите</span>
                    {plateViewportPosition?.isCustom ? (
                      <button
                        type="button"
                        className="ml-auto rounded px-1.5 py-0.5 text-[10px] font-medium text-arch-surface/70 transition hover:bg-arch-surface/10 hover:text-arch-surface"
                        title="Вернуть автоматическую позицию"
                        onPointerDown={(event) => event.stopPropagation()}
                        onClick={(event) => {
                          event.stopPropagation()
                          resetPlateDragPosition(plateRegion!.idx)
                        }}
                      >
                        ↺ авто
                      </button>
                    ) : null}
                  </div>
                ) : null}
                <div
                  className={
                    plateExpanded
                      ? `max-h-[min(70dvh,420px)] overflow-y-auto px-5 py-4 ${TRACE_PLATE_SCROLL_CLASS}`
                      : 'px-3 py-2.5 text-sm leading-snug'
                  }
                >
                  {tracePlateContent}
                </div>
              </div>
            </>,
            document.body,
          )
        : null}
    </div>
  )
}
