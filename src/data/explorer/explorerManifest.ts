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

export interface ExplorerManifest {
  cardId: string
  defaultComparisonId: string
  comparisons: ExplorerComparisonEntry[]
  updatedAt?: string
}

const base = import.meta.env.BASE_URL

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
  historicalUrl: string
  comparisonId: string
  comparisonTitle: string
}

/** Уникальные исторические срезы из manifest, по возрастанию года (для «Слоёв времени»). */
export function buildFacadeTimeSnapshots(
  manifest: ExplorerManifest,
  cardId: string,
): FacadeTimeSnapshot[] {
  const seen = new Set<string>()
  const snapshots: FacadeTimeSnapshot[] = []

  for (const entry of manifest.comparisons) {
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

  return snapshots.sort((a, b) => Number(a.year) - Number(b.year))
}

/**
 * Основное сравнение для фасада: cmp_legacy_001 в defaultComparisonId часто
 * отсутствует в списке comparisons — тогда берём cmp_005 или запись с max annotationCount.
 */
export function resolveDefaultComparisonId(manifest: ExplorerManifest): string {
  const { comparisons, defaultComparisonId } = manifest
  if (!comparisons.length) return defaultComparisonId

  const explicit = comparisons.find((c) => c.comparisonId === defaultComparisonId)
  if (explicit && !explicit.isLegacy) return explicit.comparisonId

  const preferred = comparisons.find((c) => c.comparisonId === 'cmp_005' && !c.isLegacy)
  if (preferred) return preferred.comparisonId

  const sorted = [...comparisons]
    .filter((c) => !c.isLegacy)
    .sort((a, b) => (b.annotationCount ?? 0) - (a.annotationCount ?? 0))
  return sorted[0]?.comparisonId ?? comparisons[0].comparisonId
}

export async function fetchExplorerManifest(cardId: string): Promise<ExplorerManifest | null> {
  const url = `${base}explorer/${cardId}/manifest.json`
  try {
    const res = await fetch(url, { cache: 'no-cache' })
    if (!res.ok) return null
    const data = (await res.json()) as ExplorerManifest
    if (!data?.comparisons?.length) return null
    return data
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
