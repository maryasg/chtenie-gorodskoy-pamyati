import type { ArchiviewBuildingAssets } from './archiviewAssets'

export interface ExplorerComparisonEntry {
  comparisonId: string
  title: string
  labelingLayout?: 'overlay' | 'side_by_side'
  annotationCount?: number
  isLegacy?: boolean
  historicalPhotoYear?: string
  modernPhotoYear?: string
  markedFacadeUrl: string
  labeledFacadeUrl: string
  sideBySideMarkedUrl?: string
  historicalRectifiedUrl: string
  modernRectifiedUrl: string
  modernSourceUrl?: string
  annotationsUrl: string
  facadeProjectUrl: string
}

export type FacadeTimeLayerOverlayMode = 'rectified' | 'archive'

/** Явная шкала «Слоёв времени» (если нужен порядок/источники не из auto). */
export interface ExplorerTimeLayerEntry {
  year: string
  label?: string
  title?: string
  comparisonId?: string
  historicalRectifiedUrl: string
  sourceUrl?: string
  overlayMode?: FacadeTimeLayerOverlayMode
}

export interface ExplorerManifest {
  cardId: string
  defaultComparisonId: string
  comparisons: ExplorerComparisonEntry[]
  /** Порядок слоёв на шкале; иначе — уникальные годы из comparisons. */
  timeLayers?: ExplorerTimeLayerEntry[]
  updatedAt?: string
}

const base = import.meta.env.BASE_URL

/** Скрыто на сайте, но остаётся в manifest.json для Archiview-экспорта. */
const WEBSITE_HIDDEN_COMPARISON_IDS: Record<string, string[]> = {
  MOSCOW_001: ['cmp_008'],
}

/** Слои времени, дублирующие основное сравнение (год + comparisonId). */
const WEBSITE_HIDDEN_TIME_LAYERS: Record<string, Array<{ year: string; comparisonId?: string }>> = {
  MOSCOW_001: [{ year: '1938', comparisonId: 'cmp_005' }],
}

function isHiddenTimeLayer(
  cardId: string,
  layer: { year: string; comparisonId?: string },
): boolean {
  const rules = WEBSITE_HIDDEN_TIME_LAYERS[cardId]
  if (!rules?.length) return false
  return rules.some(
    (rule) =>
      rule.year === layer.year &&
      (rule.comparisonId == null || rule.comparisonId === layer.comparisonId),
  )
}

function filterVisibleComparisons(manifest: ExplorerManifest): ExplorerComparisonEntry[] {
  const hidden = new Set(WEBSITE_HIDDEN_COMPARISON_IDS[manifest.cardId] ?? [])
  return manifest.comparisons.filter((c) => !hidden.has(c.comparisonId) && !c.isLegacy)
}

function filterVisibleTimeSnapshots(
  cardId: string,
  snapshots: FacadeTimeSnapshot[],
): FacadeTimeSnapshot[] {
  return snapshots.filter((snap) => !isHiddenTimeLayer(cardId, snap))
}

/** Убирает ошибочные дубликаты из manifest перед показом на сайте. */
export function sanitizeManifestForWebsite(manifest: ExplorerManifest): ExplorerManifest {
  const comparisons = filterVisibleComparisons(manifest)
  const timeLayers = manifest.timeLayers?.filter(
    (layer) => !isHiddenTimeLayer(manifest.cardId, layer),
  )

  let defaultComparisonId = manifest.defaultComparisonId
  const hiddenComparisons = new Set(WEBSITE_HIDDEN_COMPARISON_IDS[manifest.cardId] ?? [])
  if (hiddenComparisons.has(defaultComparisonId)) {
    defaultComparisonId = resolveDefaultComparisonId({ ...manifest, comparisons })
  }

  return {
    ...manifest,
    defaultComparisonId,
    comparisons,
    timeLayers,
  }
}

function resolveExplorerAsset(cardId: string, relPath: string): string {
  const clean = relPath.replace(/^\.\//, '').replace(/^\//, '')
  return `${base}explorer/${cardId}/${clean}`
}

export function manifestEntryToAssets(
  cardId: string,
  buildingId: string,
  entry: ExplorerComparisonEntry,
  defaults: ArchiviewBuildingAssets,
): ArchiviewBuildingAssets {
  return {
    buildingId,
    cardId,
    markedFacadeUrl: resolveExplorerAsset(cardId, entry.markedFacadeUrl),
    labeledFacadeUrl: resolveExplorerAsset(cardId, entry.labeledFacadeUrl),
    sideBySideMarkedUrl: entry.sideBySideMarkedUrl
      ? resolveExplorerAsset(cardId, entry.sideBySideMarkedUrl)
      : defaults.sideBySideMarkedUrl,
    labelingLayout: entry.labelingLayout ?? defaults.labelingLayout,
    historicalRectifiedUrl: resolveExplorerAsset(cardId, entry.historicalRectifiedUrl),
    modernRectifiedUrl: resolveExplorerAsset(cardId, entry.modernRectifiedUrl),
    modernSourceUrl: entry.modernSourceUrl
      ? resolveExplorerAsset(cardId, entry.modernSourceUrl)
      : defaults.modernSourceUrl,
    arPhotoUrl: (entry as ExplorerComparisonEntry & { arPhotoUrl?: string }).arPhotoUrl
      ? resolveExplorerAsset(cardId, (entry as ExplorerComparisonEntry & { arPhotoUrl?: string }).arPhotoUrl!)
      : defaults.arPhotoUrl,
    historicalPhotoYear: entry.historicalPhotoYear ?? defaults.historicalPhotoYear,
    modernPhotoYear: entry.modernPhotoYear ?? defaults.modernPhotoYear,
    annotationsUrl: resolveExplorerAsset(cardId, entry.annotationsUrl),
    facadeProjectUrl: resolveExplorerAsset(cardId, entry.facadeProjectUrl),
    comparisonId: entry.comparisonId,
    comparisonTitle: entry.title,
  }
}

export type FacadeTimeSnapshot = {
  year: string
  /** Подпись на кнопке шкалы (если отличается от year). */
  label?: string
  historicalUrl: string
  comparisonId: string
  comparisonTitle: string
  sourceUrl?: string
  /** rectified — призрак на выпрямленном modern; archive — отдельный архивный кадр. */
  overlayMode?: FacadeTimeLayerOverlayMode
}

function buildFacadeTimeSnapshotsFromConfig(
  manifest: ExplorerManifest,
  cardId: string,
): FacadeTimeSnapshot[] {
  return (manifest.timeLayers ?? []).map((layer) => ({
    year: layer.year,
    label: layer.label,
    historicalUrl: resolveExplorerAsset(cardId, layer.historicalRectifiedUrl),
    comparisonId: layer.comparisonId ?? `layer_${layer.year}`,
    comparisonTitle: layer.title ?? layer.label ?? layer.year,
    sourceUrl: layer.sourceUrl,
    overlayMode: layer.overlayMode ?? 'rectified',
  }))
}

/** Уникальные исторические срезы из manifest, по возрастанию года (для «Слоёв времени»). */
export function buildFacadeTimeSnapshots(
  manifest: ExplorerManifest,
  cardId: string,
): FacadeTimeSnapshot[] {
  let snapshots: FacadeTimeSnapshot[]

  if (manifest.timeLayers?.length) {
    snapshots = buildFacadeTimeSnapshotsFromConfig(manifest, cardId)
  } else {
    const seen = new Set<string>()
    snapshots = []

    for (const entry of filterVisibleComparisons(manifest)) {
      const year = entry.historicalPhotoYear?.trim()
      if (!year || seen.has(year)) continue
      seen.add(year)
      snapshots.push({
        year,
        historicalUrl: resolveExplorerAsset(cardId, entry.historicalRectifiedUrl),
        comparisonId: entry.comparisonId,
        comparisonTitle: entry.title,
      })
    }

    snapshots.sort((a, b) => Number(a.year) - Number(b.year))
  }

  return filterVisibleTimeSnapshots(cardId, snapshots)
}

/**
 * Основное сравнение для фасада: cmp_legacy_001 в defaultComparisonId часто
 * отсутствует в списке comparisons — тогда берём cmp_005 или запись с max annotationCount.
 */
export function resolveDefaultComparisonId(manifest: ExplorerManifest): string {
  const { comparisons, defaultComparisonId } = manifest
  if (!comparisons.length) return defaultComparisonId

  const visible = filterVisibleComparisons(manifest)
  if (!visible.length) return defaultComparisonId

  const explicit = visible.find((c) => c.comparisonId === defaultComparisonId)
  if (explicit && !explicit.isLegacy) return explicit.comparisonId

  const preferred = visible.find((c) => c.comparisonId === 'cmp_005' && !c.isLegacy)
  if (preferred) return preferred.comparisonId

  const sorted = [...visible]
    .filter((c) => !c.isLegacy)
    .sort((a, b) => (b.annotationCount ?? 0) - (a.annotationCount ?? 0))
  return sorted[0]?.comparisonId ?? visible[0].comparisonId
}

export async function fetchExplorerManifest(cardId: string): Promise<ExplorerManifest | null> {
  const url = `${base}explorer/${cardId}/manifest.json`
  try {
    const res = await fetch(url, { cache: 'no-cache' })
    if (!res.ok) return null
    const data = (await res.json()) as ExplorerManifest
    if (!data?.comparisons?.length) return null
    return sanitizeManifestForWebsite(data)
  } catch {
    return null
  }
}

/** Источники annotations.json для экспертной страницы — по всем сравнениям из manifest. */
export type ExpertAnnotationSource = {
  comparisonId: string
  comparisonTitle: string
  annotationsUrl: string
  annotationsRelPath: string
}

export async function fetchExpertAnnotationSources(
  cardId: string,
  fallbackAnnotationsUrl: string,
): Promise<ExpertAnnotationSource[]> {
  const manifest = await fetchExplorerManifest(cardId)
  if (!manifest?.comparisons?.length) {
    return [
      {
        comparisonId: 'default',
        comparisonTitle: 'Основное сравнение',
        annotationsUrl: fallbackAnnotationsUrl,
        annotationsRelPath: 'annotations.json',
      },
    ]
  }
  return manifest.comparisons.map((entry) => ({
    comparisonId: entry.comparisonId,
    comparisonTitle:
      entry.historicalPhotoYear && entry.modernPhotoYear
        ? `${entry.historicalPhotoYear} → ${entry.modernPhotoYear}`
        : entry.title || entry.comparisonId,
    annotationsUrl: resolveExplorerAsset(cardId, entry.annotationsUrl),
    annotationsRelPath: entry.annotationsUrl.replace(/^\.\//, ''),
  }))
}
