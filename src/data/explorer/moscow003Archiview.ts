/** Пилот Archiview: Чистопрудный 14с3 — файлы в public/explorer/MOSCOW_003/ */

const base = import.meta.env.BASE_URL

export const MOSCOW_003_EXPLORER = {
  buildingId: 'MOSCOW_003_dom_so_zveryami',
  title: 'Дом со зверями · Чистопрудный 14с3',
  markedFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade.png`,
  labeledFacadeUrl: `${base}explorer/MOSCOW_003/marked-facade-labeled.png`,
  annotationsUrl: `${base}explorer/MOSCOW_003/annotations.json`,
}

export interface ArchiviewAnnotation {
  id: number
  class: string
  label_ru: string
  comment: string
}
