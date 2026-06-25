export type BlockLayoutMetrics = {
  imageLeftPct: number
  imageTopPct: number
  imageWidthPct: number
  imageHeightPct: number
}

export type TracePlateLayout = {
  leftPct: number
  topPct: number
  transform: string
  compact: boolean
  /** width / height — 0.75 = 3:4, 1.33 = 4:3 */
  aspectRatio: number
  maxWidthPx: number
}

type RegionBBox = { minX: number; minY: number; maxX: number; maxY: number }

type TracePlateOptions = {
  bbox?: RegionBBox
  layout?: BlockLayoutMetrics
  sidebarLayout?: boolean
  cardId?: string
  regionIdx?: number
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function regionSpan(bbox?: RegionBBox): number {
  if (!bbox) return 12
  return Math.max(bbox.maxX - bbox.minX, bbox.maxY - bbox.minY)
}

function imageToBlock(
  cxPct: number,
  cyPct: number,
  layout?: BlockLayoutMetrics,
): { blockCx: number; blockCy: number; imageRightPct: number; imageLeftPct: number } {
  if (!layout) {
    return { blockCx: cxPct, blockCy: cyPct, imageRightPct: 100, imageLeftPct: 0 }
  }
  const blockCx = layout.imageLeftPct + (cxPct / 100) * layout.imageWidthPct
  const blockCy = layout.imageTopPct + (cyPct / 100) * layout.imageHeightPct
  const imageRightPct = layout.imageLeftPct + layout.imageWidthPct
  return { blockCx, blockCy, imageRightPct, imageLeftPct: layout.imageLeftPct }
}

/**
 * Плашка рядом с артефактом: перекрывает часть фото и часть списка на стыке колонок.
 */
export function tracePlatePlacement(
  cxPct: number,
  cyPct: number,
  expanded: boolean,
  options?: TracePlateOptions,
): TracePlateLayout {
  const bbox = options?.bbox
  const layout = options?.layout
  const sidebarLayout = options?.sidebarLayout ?? false
  const cardId = options?.cardId
  const regionIdx = options?.regionIdx
  const span = regionSpan(bbox)
  const regionSmall = span <= 7.5

  const { blockCx, blockCy, imageRightPct, imageLeftPct } = imageToBlock(cxPct, cyPct, layout)
  const hasSidebar = sidebarLayout && layout && imageRightPct < 98

  const aspectRatio = cyPct > 58 || cyPct < 28 ? 0.75 : cxPct < 38 ? 1.33 : 0.75

  let maxWidthPx = expanded ? 380 : 260

  let offsetX = 0
  let offsetY = 0
  if (regionSmall) {
    if (cxPct < 38) offsetX = layout ? layout.imageWidthPct * 0.08 : 8
    else if (cxPct > 62) offsetX = layout ? -layout.imageWidthPct * 0.06 : -6
    if (cyPct < 34) offsetY = layout ? layout.imageHeightPct * 0.1 : 11
    else if (cyPct > 66) offsetY = layout ? -layout.imageHeightPct * 0.1 : -11
  } else if (span > 14) {
    offsetY =
      cyPct < 50
        ? layout
          ? layout.imageHeightPct * 0.04
          : 4
        : layout
          ? -layout.imageHeightPct * 0.04
          : -4
  }

  let leftPct: number
  let topPct = blockCy + offsetY

  if (hasSidebar) {
    const seam = imageRightPct
    const atSeam = seam - 1.5
    const nearArtifact = blockCx + offsetX

    if (cxPct >= 42) {
      leftPct = atSeam
    } else {
      leftPct = Math.min(nearArtifact, atSeam + 2)
    }

    leftPct = clamp(leftPct, imageLeftPct + 14, seam + 3)
  } else {
    leftPct = clamp(blockCx + offsetX, 8, 94)
  }

  topPct = clamp(topPct, 5, expanded ? 78 : 84)

  let transform = 'translate(-50%, -50%)'
  if (expanded) {
    if (topPct < 22) transform = 'translate(-50%, 0)'
    else if (topPct > 72) transform = 'translate(-50%, -100%)'
  } else if (regionSmall) {
    if (cyPct < 40) transform = 'translate(-50%, 0)'
    else if (cyPct > 60) transform = 'translate(-50%, -100%)'
  } else if (topPct < 18) {
    transform = 'translate(-50%, 0)'
  } else if (topPct > 74) {
    transform = 'translate(-50%, -100%)'
  }

  // Ардовы: плашки #1 и #9 — как у #3, правее и шире
  if (cardId === 'MOSCOW_001' && (regionIdx === 1 || regionIdx === 9)) {
    const seam = hasSidebar ? imageRightPct : 100
    leftPct = clamp(leftPct + (layout ? layout.imageWidthPct * 0.06 : 6), imageLeftPct + 14, seam + 5)
    maxWidthPx = expanded ? 420 : 330
  }

  return {
    leftPct,
    topPct,
    transform,
    compact: !expanded,
    aspectRatio,
    maxWidthPx,
  }
}
