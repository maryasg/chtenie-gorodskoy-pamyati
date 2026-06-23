/** Готовые экспорты Archiview в public/explorer/<cardId>/ */

const base = import.meta.env.BASE_URL

export interface ArchiviewAnnotation {
  id: number
  class: string
  label_ru: string
  comment: string
  /** Optional link to curated building.memoryTraces content. */
  traceId?: string
  polygon?: [number, number][]
}

export interface ArchiviewBuildingAssets {
  buildingId: string
  cardId: string
  markedFacadeUrl: string
  labeledFacadeUrl: string
  /** 10_side_by_side_marked.png — режим «разные ракурсы» */
  sideBySideMarkedUrl?: string
  labelingLayout?: 'overlay' | 'side_by_side'
  /** 03_historical_rectified.png — для ползунка до/после */
  historicalRectifiedUrl: string
  /** 04_modern_rectified.png */
  modernRectifiedUrl: string
  /** 11_modern_source_for_site.png — исходное современное (с обрезкой, если была) */
  modernSourceUrl?: string
  /** Полевое фото для AR-preview (например 20260520_185142.jpg); разметка через H_rect_to_modern / H_rect_to_ar */
  arPhotoUrl?: string
  historicalPhotoYear?: string
  modernPhotoYear?: string
  annotationsUrl: string
  facadeProjectUrl: string
  /** Из manifest.json — какое сравнение показано */
  comparisonId?: string
  comparisonTitle?: string
}

export const ARCHIVIEW_ASSETS: Record<string, ArchiviewBuildingAssets> = {
  MOSCOW_001_kumaninykh: {
    buildingId: 'MOSCOW_001_kumaninykh',
    cardId: 'MOSCOW_001',
    markedFacadeUrl: `${base}explorer/MOSCOW_001/marked-facade.png`,
    labeledFacadeUrl: `${base}explorer/MOSCOW_001/marked-facade-labeled.png`,
    labelingLayout: 'overlay',
    historicalRectifiedUrl: `${base}explorer/MOSCOW_001/historical-rectified.png`,
    modernRectifiedUrl: `${base}explorer/MOSCOW_001/modern-rectified.png`,
    modernSourceUrl: `${base}explorer/MOSCOW_001/modern-source.png`,
    historicalPhotoYear: '1924',
    modernPhotoYear: '2026',
    annotationsUrl: `${base}explorer/MOSCOW_001/annotations.json`,
    facadeProjectUrl: `${base}explorer/MOSCOW_001/facade-project.json`,
  },
  MOSCOW_002_turgenev_library: {
    buildingId: 'MOSCOW_002_turgenev_library',
    cardId: 'MOSCOW_002',
    markedFacadeUrl: `${base}explorer/MOSCOW_002/marked-facade.png`,
    labeledFacadeUrl: `${base}explorer/MOSCOW_002/marked-facade-labeled.png`,
    labelingLayout: 'overlay',
    historicalRectifiedUrl: `${base}explorer/MOSCOW_002/historical-rectified.png`,
    modernRectifiedUrl: `${base}explorer/MOSCOW_002/modern-rectified.png`,
    historicalPhotoYear: '1934',
    modernPhotoYear: '2026',
    annotationsUrl: `${base}explorer/MOSCOW_002/annotations.json`,
    facadeProjectUrl: `${base}explorer/MOSCOW_002/facade-project.json`,
  },
  MOSCOW_003_dom_so_zveryami: {
    buildingId: 'MOSCOW_003_dom_so_zveryami',
    cardId: 'MOSCOW_003',
    markedFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade.png`,
    labeledFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade-labeled.png`,
    historicalRectifiedUrl: `${base}explorer/MOSCOW_003/historical-rectified.png`,
    modernRectifiedUrl: `${base}explorer/MOSCOW_003/modern-rectified.png`,
    modernSourceUrl: `${base}explorer/MOSCOW_003/modern-source.png`,
    arPhotoUrl: `${base}explorer/MOSCOW_003/20260520_185142.jpg`,
    historicalPhotoYear: '1911',
    modernPhotoYear: '2026',
    annotationsUrl: `${base}explorer/MOSCOW_003/annotations.json`,
    facadeProjectUrl: `${base}explorer/MOSCOW_003/facade-project.json`,
  },
  MOSCOW_004_krivokolenny: {
    buildingId: 'MOSCOW_004_krivokolenny',
    cardId: 'MOSCOW_004',
    markedFacadeUrl: `${base}explorer/MOSCOW_004/side-by-side-marked.png`,
    labeledFacadeUrl: `${base}explorer/MOSCOW_004/marked-facade-labeled.png`,
    sideBySideMarkedUrl: `${base}explorer/MOSCOW_004/side-by-side-marked.png`,
    labelingLayout: 'side_by_side',
    historicalRectifiedUrl: `${base}explorer/MOSCOW_004/historical-rectified.png`,
    modernRectifiedUrl: `${base}explorer/MOSCOW_004/modern-rectified.png`,
    historicalPhotoYear: '1989',
    modernPhotoYear: '2026',
    annotationsUrl: `${base}explorer/MOSCOW_004/annotations.json`,
    facadeProjectUrl: `${base}explorer/MOSCOW_004/facade-project.json`,
  },
}

export function getArchiviewAssets(buildingId: string): ArchiviewBuildingAssets | undefined {
  return ARCHIVIEW_ASSETS[buildingId]
}
