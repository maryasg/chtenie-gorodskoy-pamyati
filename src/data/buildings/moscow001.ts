import type { Building } from '../../types/building'

export const MOSCOW_001: Building = {
  id: 'MOSCOW_001_kumaninykh',
  cardId: 'MOSCOW_001',
  name: 'Усадьба Куманиных / Дом Ардовых',
  address: 'Москва, Большая Ордынка, 17',
  lat: 55.7425,
  lng: 37.6258,
  mapStatus: 'verified',
  style: 'Палаты XVII / усадьба XVIII–XIX',
  yearBuilt: 'XVII–XIX',
  headline: 'Палаты XVII века, перестроенные в усадьбу Куманиных → дом Ардовых; Ахматова, Янковский, Баталов',
  methodologyNote: 'Слоистый фасад: древние палаты, перестройки под усадьбу, мемориальные слои.',
  summary:
    'Здание выросло из палат XVII века, которые Куманины перестроили под свою усадебную застройку; позже здесь сформировался дом Ардовых. Характерный «слоистый» дом центра Москвы. В разное время здесь жили и работали Ахматова, Янковский, Баталов. Рядом — тяжёлая память о зоне принудработ у Иоанно-Предтеченской обители.',
  memoryTraces: [
    {
      id: 'T001',
      type: 'layer_seam',
      title: 'Швы слоёв застройки',
      period: 'XVII–XX',
      confidence: 'confirmed',
      userMessage: 'На фасаде читаются следы разных эпох кладки и перестроек.',
    },
    {
      id: 'T002',
      type: 'bricked_opening',
      title: 'Заложенные проёмы',
      period: 'разные',
      confidence: 'probable',
      userMessage: 'Типично для палат — заложенные окна и проёмы.',
    },
    {
      id: 'T003',
      type: 'memorial_sign',
      title: 'Мемориальные доски',
      period: 'современность',
      confidence: 'confirmed',
      userMessage: 'Доски Ахматовой, Баталова — современный слой памяти места.',
    },
  ],
  artifacts: [],
  timeline: [
    {
      id: 'tl-1',
      period: 'XVII–XIX',
      title: 'От палат к усадебному дому',
      whatChanged: 'Палаты XVII века перестроены под усадебный комплекс Куманиных',
      visibleToday: 'Следы ранних слоёв в кладке',
      confidence: 'confirmed',
    },
  ],
  photos: [
    { id: 'pastvu-2517403', type: 'archive', description: 'Архив PastVu', url: 'https://pastvu.com/p/2517403' },
    { id: 'shm', type: 'archive', description: 'ГИМ', url: 'https://catalog.shm.ru/entity/OBJECT/3106660' },
  ],
  hotspots: [],
  sources: [{ id: 'pastvu', name: 'PastVu', url: 'https://pastvu.com/p/2517403' }],
}
