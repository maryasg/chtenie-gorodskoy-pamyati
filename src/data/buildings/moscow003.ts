import type { Building } from '../../types/building'

export const MOSCOW_003: Building = {
  id: 'MOSCOW_003_dom_so_zveryami',
  cardId: 'MOSCOW_003',
  name: 'Дом со зверями',
  alternativeNames: ['Дом Перцова', 'Доходный дом церкви Троицы на Грязех'],
  address: 'Москва, Чистопрудный бульвар, 14, строение 3',
  lat: 55.7599,
  lng: 37.6445,
  mapStatus: 'verified',
  cardVersion: '0.3',
  cardStatus: 'pilot_in_progress',
  style: 'Модерн (русский / финский северный)',
  yearBuilt: '1908–1912',
  headline: 'Доходный дом церкви → надстройка 1945 → переделки 2000-х',
  methodologyNote:
    'Главный показательный случай пилота: советская надстройка, утраты декора, чтение слоистого фасада.',
  architect: 'Лев Кравецкий',
  protectionStatus: 'региональный памятник архитектуры',
  summary:
    'Один из ярчайших примеров московского модерна с декором «древнерусской кремли». Сохранились рельефы зверей и решётки при существенных утратах верхних частей после надстройки 1945 года.',
  verification: {
    historicalPhoto: true,
    historicalPhotoYear: '1911',
    modernPhotoYear: '2026',
    officialExpertise: [
      {
        title: 'Акт историко-культурной экспертизы (Чистопрудный бульвар, 14, стр. 3)',
        url: 'https://www.mos.ru/upload/documents/files/5859/AKTGIKEsprilChistoprydnii14str3polvalChistoprydnii14str3polval.pdf',
        issuedAt: '2019',
      },
    ],
  },
  memoryTraces: [
    {
      id: 'MOSCOW_003_T001',
      type: 'added_floor',
      title: 'Советская надстройка двух этажей',
      period: '1944–1945',
      confidence: 'confirmed',
      overallConfidence: 0.98,
      userMessage:
        '6–7 этажи — советская надстройка 1945 года (арх. Б.Л. Топаз). До неё дом был 4–5-этажным. Верхние этажи без модернового декора — виден шов и иной ритм фасада.',
    },
    {
      id: 'MOSCOW_003_T002',
      type: 'lost_tent_roof',
      title: 'Утраченная шатровая крыша левой башни',
      period: 'до 1944',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Левая башня имела островерхую шатровую кровлю — приём северного модерна. При надстройке 1945 шатёр снят.',
    },
    {
      id: 'MOSCOW_003_T003',
      type: 'lost_decoration_dated',
      title: 'Утраченный барельеф «АЦП» (1908)',
      period: 'до 1944',
      confidence: 'confirmed',
      overallConfidence: 0.92,
      userMessage:
        'Барельеф с буквами «АЦП» обозначал 1908 год в кириллической системе. Утрачен при надстройке.',
    },
    {
      id: 'MOSCOW_003_T004',
      type: 'lost_balconies',
      title: 'Утраченные балконы',
      period: '1944',
      confidence: 'probable',
      overallConfidence: 0.85,
      userMessage:
        'Балконы дореволюционного дома демонтированы при реконструкции. Следы крепежа требуют полевой проверки.',
    },
    {
      id: 'MOSCOW_003_T005',
      type: 'window_to_door_conversion',
      title: 'Окно 2-го этажа → дверь',
      period: '2000-е',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Центральное окно превращено в дверь антикварного магазина; лестница с решёткой со зверями.',
    },
    {
      id: 'MOSCOW_003_T006',
      type: 'facade_repainting',
      title: 'Перекраска фасада',
      period: '2000-е',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Охристый цвет заменён на бледно-голубовато-зелёный; барельефы выкрашены белым.',
    },
  ],
  artifacts: [
    {
      id: 'art-beasts',
      title: 'Ленточный пояс рельефов с зверями',
      period: '1908–1912',
      confidence: 'confirmed',
      location: '2–3 этаж, главный фасад',
    },
    {
      id: 'art-grilles',
      title: 'Решётки окон и лестниц со зверями',
      period: '1908–1912',
      confidence: 'confirmed',
    },
    {
      id: 'art-plaques',
      title: 'Керамические плашки с номерами квартир',
      period: '1908–1912',
      confidence: 'confirmed',
    },
    {
      id: 'art-doors',
      title: 'Стилизованные двери квартир',
      period: '1908–1912',
      confidence: 'confirmed',
    },
  ],
  timeline: [
    {
      id: 'tl-1',
      period: '1908–1912',
      title: 'Первоначальный слой',
      whatChanged: 'Снос 3-этажного дома, новый доходный дом в модерне',
      visibleToday: 'Рельефы зверей, цоколь «под камень», плашки',
      confidence: 'confirmed',
      source: 'Акт историко-культурной экспертизы (mos.ru, 2019)',
    },
    {
      id: 'tl-2',
      period: '1944–1945',
      title: 'Советская надстройка',
      whatChanged: 'Надстройка до 6–7 этажей, утраты шатра, балконов, барельефа «АЦП»',
      visibleToday: 'Шов между этажами, декор только на нижних этажах',
      confidence: 'confirmed',
      source: 'Акт историко-культурной экспертизы (mos.ru, 2019)',
    },
    {
      id: 'tl-3',
      period: '2000-е',
      title: 'Постсоветские переделки',
      whatChanged: 'Окно→дверь, перекраска фасада и барельефов',
      visibleToday: 'Дверь на 2 этаже, голубовато-зелёная штукатурка',
      confidence: 'confirmed',
      source: 'Акт историко-культурной экспертизы (mos.ru, 2019)',
    },
  ],
  photos: [
    {
      id: 'pastvu-45932',
      type: 'archive',
      description: 'До надстройки (PastVu, ~1911)',
      url: 'https://pastvu.com/p/45932',
    },
    {
      id: 'pastvu-15617',
      type: 'archive',
      description: 'Коммуналка 1970-х',
      url: 'https://pastvu.com/p/15617',
    },
    {
      id: 'current',
      type: 'facade',
      description: 'Современный фасад (полевая съёмка)',
      status: '2026',
    },
  ],
  hotspots: [
    { id: 'hs-seam', label: 'Шов надстройки', x: 12, y: 38, width: 76, height: 4, traceId: 'MOSCOW_003_T001' },
    { id: 'hs-door', label: 'Дверь (бывшее окно)', x: 44, y: 52, width: 10, height: 14, traceId: 'MOSCOW_003_T005' },
    { id: 'hs-beasts', label: 'Рельефы зверей', x: 18, y: 48, width: 64, height: 18, artifactId: 'art-beasts' },
  ],
  sources: [
    {
      id: 'S001',
      name: 'Акт историко-культурной экспертизы (PDF, mos.ru)',
      url: 'https://www.mos.ru/upload/documents/files/5859/AKTGIKEsprilChistoprydnii14str3polvalChistoprydnii14str3polval.pdf',
    },
    { id: 'S002', name: 'Узнай Москву', url: 'https://um.mos.ru/houses/dom_so_zveryami/' },
    { id: 'S003', name: 'PastVu — до надстройки', url: 'https://pastvu.com/p/45932' },
  ],
}
