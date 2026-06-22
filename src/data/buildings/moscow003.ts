import type { Building } from '../../types/building'

export const MOSCOW_003: Building = {
  id: 'MOSCOW_003_dom_so_zveryami',
  cardId: 'MOSCOW_003',
  name: 'Доходный дом церкви Троицы на Грязех / Дом со зверями',
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
    overallConfidence: 'confirmed',
    confidenceNote:
      'Архитектурные выводы по фасаду — из акта экспертизы mos.ru (2019). Визуальное сравнение до и после надстройки 1945 года: фото ~1911 (PastVu, «Визуальные материалы») и съёмка 2026 (Archiview). Публикации СМИ о здании — вспомогательный контекст, ссылки в блоке «Источники».',
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
        '6–7 этажи — советская надстройка 1945 года (арх. Б.Л. Топаз). До неё дом был 4–5-этажным. Верхние этажи без модернового декора — виден шов и иной ритм фасада.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019); сравнение фото ~1911 (PastVu) → съёмка 2026 (Archiview).',
    },
    {
      id: 'MOSCOW_003_T002',
      type: 'lost_tent_roof',
      title: 'Утраченная шатровая крыша левой башни',
      period: 'до 1944',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Левая башня имела островерхую шатровую кровлю — приём северного модерна. При надстройке 1945 шатёр снят.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019); фото ~1911 (PastVu).',
    },
    {
      id: 'MOSCOW_003_T003',
      type: 'lost_decoration_dated',
      title: 'Утраченный барельеф «АЦП» (1908)',
      period: 'до 1944',
      confidence: 'confirmed',
      overallConfidence: 0.92,
      userMessage:
        'Барельеф с буквами «АЦП» обозначал 1908 год в кириллической системе. Утрачен при надстройке.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019).',
    },
    {
      id: 'MOSCOW_003_T004',
      type: 'lost_balconies',
      title: 'Утраченные балконы',
      period: '1944',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Балкон дореволюционного дома на левой части фасада демонтирован при реконструкции и надстройке 1945 г. На довоенных фотографиях балконы с кованым ограждением читаются отчётливее.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019) — утраты балконов при надстройке; фото ~1911 (PastVu); съёмка 2026 (Archiview).',
    },
    {
      id: 'MOSCOW_003_T005',
      type: 'window_to_door_conversion',
      title: 'Окно 2-го этажа → дверь',
      period: '2000-е',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Центральное окно превращено в дверь антикварного магазина; лестница с решёткой со зверями.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019); съёмка 2026 (Archiview).',
    },
    {
      id: 'MOSCOW_003_T006',
      type: 'facade_repainting',
      title: 'Перекраска фасада',
      period: '2000-е',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Охристый цвет заменён на бледно-голубовато-зелёный; барельефы выкрашены белым.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019); съёмка 2026 (Archiview).',
    },
    {
      id: 'MOSCOW_003_T007',
      type: 'lost_decorative_grille',
      title: 'Утраченный ажурный декор на кровле',
      period: 'до 1944',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Над карнизом верхнего дореволюционного яруса был ажурный декоративный пояс — на фото PastVu (~1911) он читается отчётливо. При надстройке 1945 г. элемент снят; в акте экспертизы зафиксированы утраты декора верхних частей фасада при реконструкции.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019); фото ~1911 (PastVu); съёмка 2026 (Archiview).',
    },
    {
      id: 'MOSCOW_003_T008',
      type: 'technical_artifact',
      title: 'Лестница и перила со зверями у входа',
      period: '2000-е',
      confidence: 'confirmed',
      overallConfidence: 0.93,
      userMessage:
        'При устройстве входа в антикварный магазин смонтирована лестница с коваными перилами — со львиными фигурами и орнаментом в духе дома 1908–1912 гг. Мотив «зверей» здесь цитирует первоначальный декор фасада.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019); съёмка 2026 (Archiview).',
    },
    {
      id: 'MOSCOW_003_T009',
      type: 'new_window',
      title: 'Окно 6-го этажа надстройки',
      period: '1944–1945',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Проём появился при советской надстройке (арх. Б.Л. Топаз). Оформление упрощено по сравнению с дореволюционными окнами ниже — без модернового обрамления и рельефов.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019).',
    },
    {
      id: 'MOSCOW_003_T010',
      type: 'new_window',
      title: 'Окно на правой башне надстройки',
      period: '1944–1945',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Окно верхних этажей, устроенное в 1945 году. Верхние ярусы лишены первоначального декора северного модерна; ритм и деталировка фасада здесь иные, чем на 2–4 этажах.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019).',
    },
    {
      id: 'MOSCOW_003_T011',
      type: 'new_balcony',
      title: 'Застеклённый балкон на надстройке',
      period: '1944–1945',
      confidence: 'probable',
      overallConfidence: 0.78,
      userMessage:
        'Балконный объём на уровне 5–6 этажа не входил в первоначальный проект Л. Кравецкого — на фото ~1911 его нет. Вероятно появился при надстройке 1945 г. или в послевоенных переделках; в акте экспертизы отдельной строки по этому балкону нет.\n\nИсточник: фото ~1911 (PastVu); съёмка 2026 (Archiview); акт экспертизы (mos.ru, 2019) — общая фиксация надстройки 1945 г.',
    },
    {
      id: 'MOSCOW_003_T012',
      type: 'new_window',
      title: 'Окно на уровне шва надстройки (слева)',
      period: '1944–1945',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Окно у линии примыкания дореволюционного объёма и советской надстройки. Ниже — богатый декор модерна; выше — гладкий штукатурный пояс без рельефов зверей.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019).',
    },
    {
      id: 'MOSCOW_003_T013',
      type: 'new_window',
      title: 'Окно на уровне шва надстройки (центр)',
      period: '1944–1945',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Проём на «шве» между историческими этажами и надстроенными. Наглядно показывает смену масштаба, цвета и обработки фасада после 1945 года.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019).',
    },
    {
      id: 'MOSCOW_003_T014',
      type: 'new_window',
      title: 'Окно 6–7 этажа (правая часть)',
      period: '1944–1945',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Окно в теле советской надстройки. Прямоугольный проём без исторических наличников — характерный штрих послевоенного слоя, контрастирующий с нижними этажами.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019).',
    },
    {
      id: 'MOSCOW_003_T015',
      type: 'extension',
      title: 'Пристройка справа',
      period: 'после 1945 (ориентировочно)',
      confidence: 'probable',
      overallConfidence: 0.82,
      userMessage:
        'На фото ~1911 (PastVu) правый торец фасада ниже и уже — отдельного выступающего объёма здесь нет. На современном снимке виден пристроенный блок, который выравнивает правую часть по высоте с основным корпусом. Вероятно, его устроили вместе с надстройкой 1945 г. или чуть позже, чтобы получить полноценный этаж: левая башня на довоенных снимках выше правой части. В акте экспертизы 2019 г. пристройку отдельно не описывают — вывод по сопоставлению фотоматериалов.\n\nИсточник: фото ~1911 (PastVu); съёмка 2026 (Archiview); акт экспертизы (mos.ru, 2019) — прямого упоминания пристройки нет.',
    },
    {
      id: 'MOSCOW_003_T016',
      type: 'lost_balcony',
      title: 'Утраченный балкон (правая часть фасада)',
      period: '1944',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Балкон дореволюционного дома на этом участке фасада демонтирован при реконструкции и надстройке 1945 г. На довоенных фотографиях балконы с кованым ограждением читаются отчётливее.\n\nИсточник: акт историко-культурной экспертизы (mos.ru, 2019) — утраты балконов при надстройке; фото ~1911 (PastVu); съёмка 2026 (Archiview).',
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
    {
      id: 'smi-moslenta',
      name: 'Мослента: Львы со временем превратились в котов — история дома со зверями',
      url: 'https://moslenta.ru/city/dom-v-kotorom/lvy-so-vremenem-prevratilis-v-kotov-istoriya-stolichnogo-doma-so-zveryami-drakonov-grifonov-i-akul.htm',
    },
    {
      id: 'smi-snob',
      name: 'Snob: Жизнь в тишине московских переулков — пять знаковых домов Чистых прудов',
      url: 'https://snob.ru/style/zhizn-v-tishine-moskovskih-pereulkov-istoriya-pyati-znakovyh-domov-rajona-chistyh-prudov',
    },
    {
      id: 'smi-metro',
      name: 'Metro: Дом со зверьми долго боролся с акулами (2024-07-21)',
      url: 'https://www.gazetametro.ru/articles/dom-so-zverjami-dolgo-borolsja-s-akulami-zdanie-na-chistoprudnom-bulvare-otmechaet-115-letie-21-07-2024',
    },
    {
      id: 'smi-kp',
      name: 'Комсомольская правда (Москва): Материал о доме со зверями',
      url: 'https://www.msk.kp.ru/daily/27601/4928220/',
    },
    {
      id: 'smi-ntv',
      name: 'НТВ: Сюжет о доме со зверями на Чистопрудном бульваре',
      url: 'https://www.ntv.ru/novosti/2744643/',
    },
    {
      id: 'smi-rg',
      name: 'Российская газета: Вышли из лесов (2023-09-11)',
      url: 'https://rg.ru/2023/09/11/reg-cfo/vyshli-iz-lesov.html',
    },
  ],
}
