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
    historicalPhotoYear: entry.historicalPhotoYear ?? defaults.historicalPhotoYear,
    modernPhotoYear: entry.modernPhotoYear ?? defaults.modernPhotoYear,
    annotationsUrl: resolveExplorerAsset(cardId, entry.annotationsUrl),
    facadeProjectUrl: resolveExplorerAsset(cardId, entry.facadeProjectUrl),
    comparisonId: entry.comparisonId,
    comparisonTitle: entry.title,
  }
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

/** Источники annotations.json для кураторской страницы — по всем сравнениям из manifest. */
export type CuratorAnnotationSource = {
  comparisonId: string
  comparisonTitle: string
  annotationsUrl: string
  annotationsRelPath: string
}

export async function fetchCuratorAnnotationSources(
  cardId: string,
  fallbackAnnotationsUrl: string,
): Promise<CuratorAnnotationSource[]> {
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
