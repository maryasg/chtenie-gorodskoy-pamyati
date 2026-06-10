import type { Building } from '../../types/building'

export const MOSCOW_004: Building = {
  id: 'MOSCOW_004_krivokolenny',
  cardId: 'MOSCOW_004',
  name: 'Дом с вывеской Фалькевича',
  alternativeNames: ['Доходный дом Скальского', 'Дом с вывеской «Сжатый газ»'],
  address: 'Москва, Кривоколенный переулок, 14, строение 1',
  lat: 55.7624,
  lng: 37.637,
  mapStatus: 'verified',
  style: 'Раннее XX в.',
  yearBuilt: '1912',
  headline: 'Доходный дом Скальского: на фото 1989 вывеска не читается, в 2026 она снова видна',
  methodologyNote:
    'Сравнение 1989 и 2026 показывает, как скрытый слой вывески после реставрации снова стал видимым на фасаде.',
  summary:
    'Доходный дом Скальского (1912) в Кривоколенном переулке. Сравнение показывает важный контраст: на фото 1989 года восстановленная вывеска ещё не видна, а на съёмке 2026 года после работ 2024 года читается соседняя вывеска 1920-х с надписью «Объединение государственных кислородных заводов „Сжатый газ“». Рядом сохраняется знаменитая вывеска заводско-технической конторы инженера Фалькевича (около 1918–1919); под верхним слоем проступают более ранние следы «Политехник» / «Труженик». Реставрацию вели волонтёры трудкоммуны «Вспомнить все».',
  verification: {
    historicalPhoto: true,
    historicalPhotoYear: '1989',
    modernPhotoYear: '2026',
    mediaReports: [
      {
        outlet: 'Москвич Mag',
        title: 'Волонтёры восстановили в Кривоколенном вывеску 1920-х годов, найденную под слоями штукатурки',
        url: 'https://moskvichmag.ru/gorod/volontery-vosstanovili-v-krivokolennom-vyvesku-1920-h-godov-najdennuyu-pod-sloyami-shtukaturki/',
        issuedAt: '2024-12-05',
      },
    ],
  },
  memoryTraces: [
    {
      id: 'T001',
      type: 'preserved_signage',
      title: 'Вывеска «Заводско-техническая контора. Инженер Фалькевич»',
      period: 'около 1918–1919',
      confidence: 'confirmed',
      userMessage:
        'Одна из самых узнаваемых сохранённых вывесок Москвы; в 2015 году уже реставрировали, в 2024 — соседняя находка при ремонте фасада.',
    },
    {
      id: 'T002',
      type: 'preserved_signage',
      title: 'Вывеска «Сжатый газ»',
      period: '1923–1924',
      confidence: 'confirmed',
      userMessage:
        'На фото 1989 года эта вывеска не читается; после обнаружения под штукатуркой и работ 2024 года на фото 2026 года видна надпись «Объединение государственных кислородных заводов „Сжатый газ“».',
    },
    {
      id: 'T003',
      type: 'ghost_sign_layer',
      title: 'Нижний слой «Политехник» / «Труженик»',
      period: 'начало 1920-х',
      confidence: 'probable',
      userMessage:
        'Под верхней вывеской проступает более ранняя техническая контора «Политехник» и подпись товарищества «Труженик» (по материалам реставраторов).',
    },
    {
      id: 'T004',
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
      period: '1912',
      title: 'Дом Скальского',
      whatChanged: 'Постройка доходного дома',
      visibleToday: 'Каменный фасад переулка',
      confidence: 'confirmed',
      source: 'Москвич Mag, 2024',
    },
    {
      id: 'tl-2',
      period: '1918–1924',
      title: 'Слои вывесок',
      whatChanged: 'Фалькевич, затем «Политехник» / «Сжатый газ»',
      visibleToday: 'Многослойные надписи на фасаде',
      confidence: 'confirmed',
      source: 'Москвич Mag, 2024',
    },
    {
      id: 'tl-3',
      period: '2024',
      title: 'Реставрация вывески «Сжатый газ»',
      whatChanged: 'Восстановление волонтёрами «Вспомнить все»: в сравнении 1989 → 2026 появляется читаемая вывеска',
      visibleToday: 'На современном фото 2026 года вывеска читается; на фото 1989 года она не видна',
      confidence: 'confirmed',
      source: 'Москвич Mag, 2024-12-05',
    },
  ],
  photos: [
    { id: 'pastvu-55243', type: 'archive', description: 'Архивное фото 1989: вывеска ещё не читается', url: 'https://pastvu.com/p/55243' },
    { id: 'pastvu-1307052', type: 'archive', description: 'Архив', url: 'https://pastvu.com/p/1307052' },
  ],
  hotspots: [
    { id: 'hs-sign-falkevich', label: 'Вывеска Фалькевича', x: 30, y: 55, width: 40, height: 12, traceId: 'T001' },
    { id: 'hs-sign-gas', label: 'Вывеска «Сжатый газ»', x: 55, y: 50, width: 25, height: 14, traceId: 'T002' },
  ],
  sources: [
    { id: 'pastvu', name: 'PastVu', url: 'https://pastvu.com/p/55243' },
    {
      id: 'moskvichmag-2024',
      name: 'Москвич Mag',
      url: 'https://moskvichmag.ru/gorod/volontery-vosstanovili-v-krivokolennom-vyvesku-1920-h-godov-najdennuyu-pod-sloyami-shtukaturki/',
    },
  ],
}
