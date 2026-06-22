import type { Building } from '../../types/building'

const EXPERTISE_ACT_URL =
  'https://www.mos.ru/upload/documents/files/6285/BolshayaOrdinkayld17str1kv13d17str1d19str1(chast)Pyatnickayayld14str1213d12str4(31052019).pdf'

const EXPERTISE_SOURCE = 'Акт историко-культурной экспертизы (mos.ru, 2019)'

export const MOSCOW_001: Building = {
  id: 'MOSCOW_001_kumaninykh',
  cardId: 'MOSCOW_001',
  name: 'Усадьба Куманиных / Дом Ардовых',
  address: 'Москва, Большая Ордынка, 17, стр. 1',
  lat: 55.7425,
  lng: 37.6258,
  mapStatus: 'verified',
  cardVersion: '0.2',
  style: 'Палаты XVIII / усадьба XVIII–XIX',
  yearBuilt: 'XVII–XIX',
  headline: 'Палаты XVII века, перестроенные в усадьбу Куманиных → дом Ардовых; Ахматова, Янковский, Баталов',
  methodologyNote: 'Слоистый фасад: древние палаты, перестройки под усадьбу, мемориальные слои.',
  protectionStatus: 'памятник архитектуры регионального значения',
  summary:
    'Здание выросло из палат XVII–XVIII веков, которые Куманины перестроили под свою усадебную застройку; позже здесь сформировался дом Ардовых. Характерный «слоистый» дом центра Москвы. В разное время здесь жили и работали Ахматова, Янковский, Баталов. Рядом — тяжёлая память о зоне принудработ у Иоанно-Предтеченской обители.',
  verification: {
    historicalPhoto: true,
    historicalPhotoYear: '1924',
    modernPhotoYear: '2026',
    officialExpertise: [
      {
        title: 'Акт историко-культурной экспертизы (Большая Ордынка, 17, стр. 1)',
        url: EXPERTISE_ACT_URL,
        issuedAt: '2019',
      },
    ],
  },
  memoryTraces: [
    {
      id: 'T001',
      type: 'layer_seam',
      title: 'Швы слоёв застройки',
      period: 'XVIII–XX',
      confidence: 'confirmed',
      overallConfidence: 0.92,
      userMessage:
        'В кладке и ритме фасада читаются палаты XVIII века, усадебные перестройки XIX века и поздние вмешательства XX века.',
    },
    {
      id: 'T002',
      type: 'added_floor',
      title: 'Советская надстройка этажей (1938)',
      period: '1938',
      confidence: 'confirmed',
      overallConfidence: 0.95,
      userMessage:
        'Двухэтажная усадебная часть надстроена до пяти этажей; верхние ярусы получили облик типового советского жилого дома. На фасаде виден шов между старым объёмом и надстройкой.',
    },
    {
      id: 'T003',
      type: 'bricked_opening',
      title: 'Заложенные и изменённые проёмы',
      period: 'XIX–XX',
      confidence: 'confirmed',
      overallConfidence: 0.9,
      userMessage:
        'Часть окон заложена, появились новые проёмы и переделанные входы — типичный след многослойной городской застройки и поздних ремонтов.',
    },
    {
      id: 'T004',
      type: 'changed_entrance',
      title: 'Входы, переделанные в окна',
      period: 'XX в.',
      confidence: 'confirmed',
      overallConfidence: 0.93,
      userMessage:
        'На нижнем этаже отдельные входы превращены в оконные проёмы — след приспособления дома под коммунальное и квартирное использование.',
    },
    {
      id: 'T005',
      type: 'new_balcony',
      title: 'Новые балконы',
      period: 'XX в.',
      confidence: 'probable',
      overallConfidence: 0.85,
      userMessage:
        'На фасаде появились балконные устройства, не характерные для первоначальной усадебной части.',
    },
    {
      id: 'T006',
      type: 'memorial_sign',
      title: 'Мемориальные доски и память места',
      period: 'современность',
      confidence: 'confirmed',
      overallConfidence: 0.98,
      userMessage:
        'Доски Ахматовой, Баталова и другие мемориальные знаки — современный слой памяти о жильцах и гостях дома (в т.ч. кв. 13, семья Ардовых).',
    },
  ],
  artifacts: [
    {
      id: 'art-palaty',
      title: 'Палаты середины XVIII века',
      period: 'XVIII в.',
      confidence: 'confirmed',
      location: 'центральная дворовая секция',
    },
    {
      id: 'art-fence',
      title: 'Ограда вдоль Ордынки',
      period: 'XIX в.',
      confidence: 'confirmed',
      location: 'линия улицы',
    },
    {
      id: 'art-memorial',
      title: 'Мемориальные таблички',
      period: 'XX–XXI',
      confidence: 'confirmed',
    },
  ],
  timeline: [
    {
      id: 'tl-1',
      period: 'середина XVIII в.',
      title: 'Палатный слой',
      whatChanged: 'Сформирована центральная часть из палат середины XVIII века',
      visibleToday: 'Старые объёмы и кладка в центральной секции, «дворовой» характер застройки',
      confidence: 'confirmed',
      source: EXPERTISE_SOURCE,
    },
    {
      id: 'tl-2',
      period: 'конец XVIII — XIX в.',
      title: 'Усадьба Куманиных',
      whatChanged:
        'Дом расширен и перестроен под купеческую усадьбу; после пожара 1812 года — очередная реконструкция',
      visibleToday: 'Слоистая кладка, следы заложенных проёмов, усадебная ограда',
      confidence: 'confirmed',
      source: EXPERTISE_SOURCE,
    },
    {
      id: 'tl-3',
      period: '1938',
      title: 'Советская надстройка',
      whatChanged:
        'К усадебному объёму добавлены этажи; здание приобрело облик пятиэтажного жилого дома конструктивизма / раннего сталинского периода',
      visibleToday: 'Верхние этажи без усадебного декора, шов между старым и новым объёмом',
      confidence: 'confirmed',
      source: EXPERTISE_SOURCE,
    },
    {
      id: 'tl-4',
      period: 'XX — XXI в.',
      title: 'Коммунальные переделки и память',
      whatChanged:
        'Переделки входов и проёмов, балконы; мемориальные таблички (Ахматова, Баталов и др.), память о кв. 13',
      visibleToday: 'Изменённые входы, новые окна и балконы; мемориальные знаки на фасаде и во дворе',
      confidence: 'confirmed',
      source: EXPERTISE_SOURCE,
    },
  ],
  photos: [
    {
      id: 'pastvu-2517403',
      type: 'archive',
      description: 'Архив PastVu (1920-е)',
      url: 'https://pastvu.com/p/2517403',
    },
    { id: 'shm', type: 'archive', description: 'ГИМ', url: 'https://catalog.shm.ru/entity/OBJECT/3106660' },
    {
      id: 'current',
      type: 'facade',
      description: 'Современный фасад (полевая съёмка)',
      status: '2026',
    },
  ],
  hotspots: [],
  sources: [
    {
      id: 'S001',
      name: 'Акт историко-культурной экспертизы (PDF, mos.ru)',
      url: EXPERTISE_ACT_URL,
    },
    { id: 'S002', name: 'Узнай Москву', url: 'https://um.mos.ru/houses/usadba_kumaninykh/' },
    { id: 'S003', name: 'PastVu', url: 'https://pastvu.com/p/2517403' },
    { id: 'S004', name: 'ГИМ', url: 'https://catalog.shm.ru/entity/OBJECT/3106660' },
  ],
}
