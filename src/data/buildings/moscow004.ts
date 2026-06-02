import type { Building } from '../../types/building'

export const MOSCOW_004: Building = {
  id: 'MOSCOW_004_krivokolenny',
  cardId: 'MOSCOW_004',
  name: 'Дом с вывеской Фалькевича',
  address: 'Москва, Кривоколенный переулок, 14, строение 1',
  lat: 55.7624,
  lng: 37.637,
  mapStatus: 'verified',
  style: 'Раннее XX в.',
  yearBuilt: '1910-е',
  headline: 'Вывеска «Заводско-техническая контора. Инженер Фалькевич»',
  methodologyNote: 'Сохранённая дореволюционная вывеска и окно→дверь.',
  summary:
    'Редкий случай сохранившейся вывески 1910-х и переделки оконного проёма. Слои краски и ghost signs — поле для исследователя.',
  memoryTraces: [
    {
      id: 'T001',
      type: 'preserved_signage',
      title: 'Сохранившаяся вывеска',
      period: '1910-е',
      confidence: 'confirmed',
      userMessage:
        'Вывеска «Заводско-техническая контора. Инженер Фалькевич» — главный след памяти.',
    },
    {
      id: 'T002',
      type: 'window_to_door_conversion',
      title: 'Окно → дверь',
      period: 'уточняется',
      confidence: 'needs_verification',
      userMessage: 'Проём переделан под дверь; точная дата требует архивного подтверждения.',
    },
  ],
  artifacts: [],
  timeline: [
    {
      id: 'tl-1',
      period: '1910-е',
      title: 'Дореволюционная вывеска',
      whatChanged: 'Размещение рекламы конторы',
      visibleToday: 'Сохранившаяся надпись на фасаде',
      confidence: 'confirmed',
    },
  ],
  photos: [
    { id: 'pastvu-55243', type: 'archive', description: 'Архив', url: 'https://pastvu.com/p/55243' },
    { id: 'pastvu-1307052', type: 'archive', description: 'Архив', url: 'https://pastvu.com/p/1307052' },
  ],
  hotspots: [
    { id: 'hs-sign', label: 'Вывеска Фалькевича', x: 30, y: 55, width: 40, height: 12, traceId: 'T001' },
  ],
  sources: [{ id: 'pastvu', name: 'PastVu', url: 'https://pastvu.com/p/55243' }],
}
