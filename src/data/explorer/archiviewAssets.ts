/** Готовые экспорты Archiview в public/explorer/<cardId>/ */

const base = import.meta.env.BASE_URL

export interface ArchiviewAnnotation {
  id: number
  class: string
  label_ru: string
  comment: string
  polygon?: [number, number][]
}

export interface ArchiviewBuildingAssets {
  buildingId: string
  cardId: string
  markedFacadeUrl: string
  labeledFacadeUrl: string
  /** 03_historical_rectified.png — для ползунка до/после */
  historicalRectifiedUrl: string
  /** 04_modern_rectified.png */
  modernRectifiedUrl: string
  historicalPhotoYear?: string
  modernPhotoYear?: string
  annotationsUrl: string
  facadeProjectUrl: string
}

export const ARCHIVIEW_ASSETS: Record<string, ArchiviewBuildingAssets> = {
  MOSCOW_003_dom_so_zveryami: {
    buildingId: 'MOSCOW_003_dom_so_zveryami',
    cardId: 'MOSCOW_003',
    markedFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade.png`,
    labeledFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade-labeled.png`,
    historicalRectifiedUrl: `${base}explorer/MOSCOW_003/historical-rectified.png`,
    modernRectifiedUrl: `${base}explorer/MOSCOW_003/modern-rectified.png`,
    historicalPhotoYear: '1911',
    modernPhotoYear: '2026',
    annotationsUrl: `${base}explorer/MOSCOW_003/annotations.json`,
    facadeProjectUrl: `${base}explorer/MOSCOW_003/facade-project.json`,
  },
}

export function getArchiviewAssets(buildingId: string): ArchiviewBuildingAssets | undefined {
  return ARCHIVIEW_ASSETS[buildingId]
}
