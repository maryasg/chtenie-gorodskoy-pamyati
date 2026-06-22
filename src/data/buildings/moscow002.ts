import type { Building } from '../../types/building'

export const MOSCOW_002: Building = {
  id: 'MOSCOW_002_turgenev_library',
  cardId: 'MOSCOW_002',
  name: 'Доходный дом А.А. Бирюковой-Валерьяновой / МГБ им. И.С. Тургенева',
  alternativeNames: ['Тургеневская библиотека', 'Тургеневка'],
  address: 'Москва, Бобров переулок, 6, строение 1',
  lat: 55.7651,
  lng: 37.6344,
  mapStatus: 'verified',
  cardVersion: '0.2',
  style: 'Палаты XVII + надстройка 2003',
  yearBuilt: 'XVII / 2003',
  architect: 'бюро М. М. Асадова (надстройка 2003)',
  protectionStatus: 'памятник архитектуры регионального значения',
  headline: 'Палаты XVII века → публичная библиотека → надстройка бюро Асадова «дом над домом»',
  methodologyNote:
    'Слоистый фасад: древние палаты, библиотечные перестройки XIX–XX веков и современная надстройка 2003 года. Сравнение Archiview: архив 1934 → съёмка 2026.',
  summary:
    'В основе здания — палаты XVII века. В XIX веке здесь сформировался доходный дом А. А. Бирюковой-Валерьяновой. С конца XIX века дом связан с историей публичного чтения: по благотворительной инициативе вдовы Морозовой здесь разместилась одна из первых московских библиотек для рабочих; позже — Московская городская библиотека имени И. С. Тургенева («Тургеневка»), один из узнаваемых культурных адресов центра. При реставрации и строительстве надстройки 2003 года (архитекторы бюро М. М. Асадова) на фасаде вновь проступили фрагменты исторической кладки и объёмов — «дом над домом», где современный корпус опирается на сохранённое историческое ядро.',
  verification: {
    historicalPhoto: true,
    historicalPhotoYear: '1934',
    modernPhotoYear: '2026',
    overallConfidence: 'confirmed',
    confidenceNote:
      'История здания и библиотеки — по официальной справке МГБ им. И. С. Тургенева (не СМИ) и публикациям в прессе. Визуальное сравнение слоёв фасада: архив 1934 (PastVu, см. «Визуальные материалы») и полевая съёмка 2026 (Archiview). Статьи СМИ — вспомогательный контекст, ссылки в блоке «Источники».',
  },
  memoryTraces: [
    {
      id: 'T001',
      type: 'layered_facade',
      title: 'Слоистый фасад',
      period: 'XVII–XXI',
      confidence: 'confirmed',
      userMessage:
        'Граница между палатами XVII века, поздними перестройками доходного дома и библиотечными слоями XIX–XX веков. На фасаде читается смена материалов, ритма окон и высоты корпуса.',
    },
    {
      id: 'T002',
      type: 'modern_superstructure',
      title: 'Надстройка 2003',
      period: '2003',
      confidence: 'confirmed',
      userMessage:
        'Надстройка бюро М. М. Асадова — показательный пример архитектуры «дом над домом»: новый объём поднят над сохранённым историческим ядром, не скрывая его полностью.',
    },
    {
      id: 'T003',
      type: 'restored_layer',
      title: 'Исторический фасад, открытый при реставрации',
      period: '2000-е',
      confidence: 'confirmed',
      userMessage:
        'При реставрационных работах на фасаде вновь проступили фрагменты исторической кладки и объёмов — след более ранних слоёв, скрытых штукатуркой и поздними наслоениями.',
    },
  ],
  artifacts: [],
  timeline: [
    {
      id: 'tl-1',
      period: 'XVII в.',
      title: 'Палаты',
      whatChanged: 'Каменное ядро здания — палаты XVII века',
      visibleToday: 'Нижние объёмы и фрагменты кладки в теле современного корпуса',
      confidence: 'confirmed',
      source: 'Публикации о Тургеневской библиотеке; сравнение 1934 → 2026 (Archiview)',
    },
    {
      id: 'tl-2',
      period: 'XIX в.',
      title: 'Доходный дом Бирюковой-Валерьяновой',
      whatChanged: 'Перестройка и надстройка доходного дома вокруг исторического ядра',
      visibleToday: 'Средние ярусы фасада, смена ритма окон',
      confidence: 'probable',
      source: 'Исторические справки о здании; архив 1934 (PastVu)',
    },
    {
      id: 'tl-3',
      period: 'конец XIX — нач. XX в.',
      title: 'Библиотека для рабочих',
      whatChanged: 'По благотворительной инициативе вдовы Морозовой здесь размещается читальня для рабочих',
      visibleToday: 'Культурная функция здания — публичная библиотека',
      confidence: 'confirmed',
      source: 'Милосердие.ру; Москвич Mag',
    },
    {
      id: 'tl-4',
      period: 'XX в.',
      title: 'МГБ им. И. С. Тургенева',
      whatChanged: 'Здание становится одной из центральных городских библиотек Москвы',
      visibleToday: '«Тургеневка» как культурный адрес Бобрового переулка',
      confidence: 'confirmed',
      source: 'Публикации СМИ о библиотеке',
    },
    {
      id: 'tl-5',
      period: '2003',
      title: 'Современная надстройка',
      whatChanged: 'Новый объём над историческим ядром (бюро М. М. Асадова)',
      visibleToday: 'Архитектура «дом над домом»',
      confidence: 'confirmed',
      source: 'Archiview 2026; публикации о реконструкции',
    },
  ],
  photos: [
    {
      id: 'pastvu-2053853',
      type: 'archive',
      description: 'Филатов, 1934 (PastVu)',
      url: 'https://pastvu.com/p/2053853',
    },
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
      id: 'turgenev-history',
      name: 'МГБ им. И. С. Тургенева — история библиотеки',
      url: 'https://turgenev.ru/o-biblioteke/istoriya/',
    },
    {
      id: 'smi-moskvichmag',
      name: 'Москвич Mag: Дом недели — Тургеневская библиотека в Бобровом переулке',
      url: 'https://moskvichmag.ru/gorod/dom-nedeli-turgenevskaya-biblioteka-v-bobrovom-pereulke/',
    },
    {
      id: 'smi-miloserdie',
      name: 'Милосердие.ру: Легендарная «Тургеневка» — благотворительный проект вдовы Морозовой',
      url: 'https://www.miloserdie.ru/article/legendarnaya-turgenevka-blagotvoritelnyj-proekt-morozovskoj-vdovy/',
    },
    {
      id: 'smi-tj',
      name: 'Т—Ж: Необычные московские библиотеки',
      url: 'https://t-j.ru/list/moscow-libraries/',
    },
    {
      id: 'smi-mir24',
      name: 'МИР 24: Девять необычных библиотек Москвы',
      url: 'https://mir24.tv/articles/16362147/devyat-neobychnyh-bibliotek-moskvy',
    },
    {
      id: 'smi-thecity',
      name: 'The City: Материал о Тургеневской библиотеке',
      url: 'https://thecity.m24.ru/articles/8414',
    },
  ],
}
