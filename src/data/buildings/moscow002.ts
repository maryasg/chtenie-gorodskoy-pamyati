import type { Building } from '../../types/building'

export const MOSCOW_002: Building = {
  id: 'MOSCOW_002_turgenev_library',
  cardId: 'MOSCOW_002',
  name: 'Тургеневская библиотека',
  address: 'Москва, Бобров переулок, 6, строение 1',
  lat: 55.7635,
  lng: 37.6363,
  mapStatus: 'verified',
  style: 'Палаты XVII + надстройка 2003',
  yearBuilt: 'XVII / 2003',
  headline: 'Палаты → библиотека; надстройка бюро Асадова',
  methodologyNote: 'Современная надстройка «дом над домом» как новый слой.',
  summary:
    'Палаты XVII века в основе. Перестройка 2003 года — показательный пример включения исторической структуры в современное здание.',
  memoryTraces: [
    {
      id: 'T001',
      type: 'layered_facade',
      title: 'Слоистый фасад',
      period: 'XVII–XXI',
      confidence: 'confirmed',
      userMessage: 'Граница между палатами XVII в. и поздними этажами.',
    },
    {
      id: 'T002',
      type: 'modern_superstructure',
      title: 'Надстройка 2003',
      period: '2003',
      confidence: 'confirmed',
      userMessage: 'Надстройка бюро Асадова — «дом над домом».',
    },
  ],
  artifacts: [],
  timeline: [
    {
      id: 'tl-1',
      period: '2003',
      title: 'Современная надстройка',
      whatChanged: 'Новый объём над историческим ядром',
      visibleToday: 'Архитектура «дом над домом»',
      confidence: 'confirmed',
    },
  ],
  photos: [
    {
      id: 'pastvu-2053853',
      type: 'archive',
      description: 'Филатов, 1934',
      url: 'https://pastvu.com/p/2053853',
    },
  ],
  hotspots: [],
  sources: [{ id: 'pastvu', name: 'PastVu', url: 'https://pastvu.com/p/2053853' }],
}
