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
): { blockCx: number; blockCy: number; imageRightPct: number } {
  if (!layout) {
    return { blockCx: cxPct, blockCy: cyPct, imageRightPct: 100 }
  }
  const blockCx = layout.imageLeftPct + (cxPct / 100) * layout.imageWidthPct
  const blockCy = layout.imageTopPct + (cyPct / 100) * layout.imageHeightPct
  const imageRightPct = layout.imageLeftPct + layout.imageWidthPct
  return { blockCx, blockCy, imageRightPct }
}

/**
 * Плашка рядом с артефактом: перекрывает часть фото и часть списка.
 * Пропорции ~3:4 или 4:3 в зависимости от положения подсветки.
 */
export function tracePlatePlacement(
  cxPct: number,
  cyPct: number,
  expanded: boolean,
  options?: TracePlateOptions,
): TracePlateLayout {
  const bbox = options?.bbox
  const layout = options?.layout
  const span = regionSpan(bbox)
  const regionSmall = span <= 7.5

  const { blockCx, blockCy, imageRightPct } = imageToBlock(cxPct, cyPct, layout)
  const hasSidebar = layout ? imageRightPct < 98 : false

  const nearSidebar = hasSidebar && blockCx > imageRightPct * 0.82
  const aspectRatio =
    nearSidebar || cyPct > 58 || cyPct < 28
      ? 0.75
      : blockCx < imageRightPct * 0.38
        ? 1.33
        : 0.75

  const maxWidthPx = expanded ? 380 : 260

  let offsetX = 0
  let offsetY = 0
  if (regionSmall) {
    if (cxPct < 38) offsetX = layout ? layout.imageWidthPct * 0.09 : 9
    else if (cxPct > 62) offsetX = layout ? -layout.imageWidthPct * 0.09 : -9
    if (cyPct < 34) offsetY = layout ? layout.imageHeightPct * 0.1 : 11
    else if (cyPct > 66) offsetY = layout ? -layout.imageHeightPct * 0.1 : -11
  } else if (span > 14) {
    offsetY = cyPct < 50 ? (layout ? layout.imageHeightPct * 0.04 : 4) : layout ? -layout.imageHeightPct * 0.04 : -4
  }

  let leftPct = blockCx + offsetX
  let topPct = blockCy + offsetY

  if (nearSidebar && hasSidebar) {
    leftPct = clamp(leftPct, imageRightPct * 0.72, imageRightPct + 5)
  } else {
    leftPct = clamp(leftPct, 8, Math.min(94, imageRightPct * 0.95))
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

  return {
    leftPct,
    topPct,
    transform,
    compact: !expanded,
    aspectRatio,
    maxWidthPx,
  }
}
