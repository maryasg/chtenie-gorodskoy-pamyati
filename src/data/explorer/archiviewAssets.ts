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
  annotationsUrl: string
  facadeProjectUrl: string
}

export const ARCHIVIEW_ASSETS: Record<string, ArchiviewBuildingAssets> = {
  MOSCOW_003_dom_so_zveryami: {
    buildingId: 'MOSCOW_003_dom_so_zveryami',
    cardId: 'MOSCOW_003',
    markedFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade.png`,
    labeledFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade-labeled.png`,
    annotationsUrl: `${base}explorer/MOSCOW_003/annotations.json`,
    facadeProjectUrl: `${base}explorer/MOSCOW_003/facade-project.json`,
  },
}

export function getArchiviewAssets(buildingId: string): ArchiviewBuildingAssets | undefined {
  return ARCHIVIEW_ASSETS[buildingId]
}
