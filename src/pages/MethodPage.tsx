import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

const PIPELINE = [
  {
    step: '1',
    title: 'Собрать пару изображений',
    text: 'Историческое фото и современная съёмка одного фасада выбираются куратором. Важно, чтобы была понятна плоскость фасада и видимые опорные точки.',
  },
  {
    step: '2',
    title: 'Выпрямить фасад в Archiview',
    text: 'В программе отмечаются четыре угла или рабочая область. Archiview приводит фасад к плоскому виду, чтобы можно было сравнивать эпохи.',
  },
  {
    step: '3',
    title: 'Сравнить слои',
    text: 'Для близких ракурсов используется overlay, для разных ракурсов - side-by-side. Это помогает не смешивать разные системы координат.',
  },
  {
    step: '4',
    title: 'Разметить следы памяти',
    text: 'Куратор обводит зоны изменений: надстройки, заложенные проёмы, утраты декора, вывески, мемориальные слои.',
  },
  {
    step: '5',
    title: 'Экспортировать на сайт',
    text: 'Archiview копирует изображения, annotations.json и facade-project.json в public/explorer/MOSCOW_NNN. После Push сайт получает новую разметку.',
  },
  {
    step: '6',
    title: 'Показать публичную карточку',
    text: 'React-сайт связывает фасад, интерактивную подсветку, тексты карточки, источники, таймлайн и маршрут экскурсии.',
  },
]

const TECH_STACK = [
  ['Frontend', 'React + TypeScript + Vite'],
  ['Карта', 'Leaflet + OpenStreetMap'],
  ['Данные карточек', 'src/data/buildings/*.ts'],
  ['Фасады и разметка', 'public/explorer/MOSCOW_NNN/'],
  ['Инструмент подготовки', 'Python / OpenCV / Tkinter: tools/archiview-cv/'],
  ['Публикация', 'GitHub Pages через GitHub Actions'],
]

const FILES = [
  ['annotations.json', 'полигоны, подписи и типы следов'],
  ['facade-project.json', 'матрица переноса координат и параметры сравнения'],
  ['marked-facade.png', 'основная картинка фасада с номерами'],
  ['historical-rectified.png / modern-rectified.png', 'пара для ползунка “история - сегодня”'],
  ['side-by-side-marked.png', 'режим разных ракурсов для вывесок и сложных случаев'],
]

const LIMITS = [
  'AI-исследователь на сайте сейчас показывает сценарий будущей функции, а не реальное машинное распознавание.',
  'AR-preview - это визуальная симуляция слоёв времени без камеры и геопривязки.',
  'Координаты подсветки зависят от правильного режима экспорта: overlay, legacy overlay или side-by-side.',
  'Исторические выводы требуют источников и кураторской проверки; сайт не заменяет экспертизу.',
]

const DEMO_CASES = [
  {
    title: 'Дом со зверями',
    to: '/building/MOSCOW_003_dom_so_zveryami',
    text: 'Главный показательный кейс: надстройка, утраты декора, сравнение 1911 и 2026 годов.',
  },
  {
    title: 'Усадьба Куманиных / Дом Ардовых',
    to: '/building/MOSCOW_001_kumaninykh',
    text: 'Слоистый фасад: палаты, усадебная перестройка, культурная и мемориальная память.',
  },
  {
    title: 'Дом с вывеской Фалькевича',
    to: '/building/MOSCOW_004_krivokolenny',
    text: 'Side-by-side для разных ракурсов и чтения городских “ghost signs”.',
  },
]

function MethodSection({
  title,
  kicker,
  children,
}: {
  title: string
  kicker?: string
  children: ReactNode
}) {
  return (
    <section className="arch-section">
      {kicker ? <p className="arch-kicker mb-1">{kicker}</p> : null}
      <h2 className="arch-section-title mb-4">{title}</h2>
      {children}
    </section>
  )
}

export function MethodPage() {
  return (
    <div className="space-y-6">
      <header className="arch-section overflow-hidden border-arch-green/20 bg-gradient-to-br from-arch-green-deep to-arch-green text-arch-surface">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-arch-gold">Техническая методология</p>
        <h1 className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight">
          Как фасад превращается в интерактивную городскую память
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-arch-surface/85">
          Проект соединяет кураторское чтение архитектуры, компьютерное выпрямление фасадов и
          публичный сайт. Главная идея: показать не только текст об истории здания, но и конкретные
          места на фасаде, где эта история видна сегодня.
        </p>
      </header>

      <MethodSection title="Короткая схема" kicker="Пайплайн">
        <div className="grid gap-3 md:grid-cols-3">
          {PIPELINE.map((item) => (
            <article key={item.step} className="rounded-xl border border-arch-line bg-arch-surface-2/40 p-4">
              <div className="mb-3 flex items-center gap-2">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-arch-green-deep text-sm font-bold text-arch-surface">
                  {item.step}
                </span>
                <h3 className="font-semibold text-arch-green-deep">{item.title}</h3>
              </div>
              <p className="text-sm leading-relaxed text-arch-ink/80">{item.text}</p>
            </article>
          ))}
        </div>
      </MethodSection>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <MethodSection title="Из чего состоит система" kicker="Архитектура">
          <dl className="divide-y divide-arch-line text-sm">
            {TECH_STACK.map(([term, desc]) => (
              <div key={term} className="grid gap-1 py-3 sm:grid-cols-[11rem_1fr]">
                <dt className="font-semibold text-arch-green-deep">{term}</dt>
                <dd className="text-arch-ink/80">{desc}</dd>
              </div>
            ))}
          </dl>
        </MethodSection>

        <MethodSection title="Что лежит в экспорте" kicker="Файлы">
          <ul className="space-y-3 text-sm">
            {FILES.map(([name, desc]) => (
              <li key={name} className="rounded-lg border border-arch-line bg-arch-surface-2/40 p-3">
                <code className="font-semibold text-arch-green-deep">{name}</code>
                <p className="mt-1 text-arch-ink/75">{desc}</p>
              </li>
            ))}
          </ul>
        </MethodSection>
      </div>

      <MethodSection title="Как сайт защищается от съехавшей подсветки" kicker="Контроль качества">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-arch-line bg-arch-green-soft p-4">
            <h3 className="font-semibold text-arch-green-deep">Overlay</h3>
            <p className="mt-2 text-sm text-arch-ink/80">
              Если картинка фасада совпадает с размером разметки, полигоны кладутся напрямую.
            </p>
          </div>
          <div className="rounded-xl border border-arch-line bg-arch-green-soft p-4">
            <h3 className="font-semibold text-arch-green-deep">Legacy overlay</h3>
            <p className="mt-2 text-sm text-arch-ink/80">
              Если размеры не совпадают, сайт использует матрицу <code>H_rect_to_modern</code> и
              переносит координаты на фактическую картинку.
            </p>
          </div>
          <div className="rounded-xl border border-arch-line bg-arch-green-soft p-4">
            <h3 className="font-semibold text-arch-green-deep">Side-by-side</h3>
            <p className="mt-2 text-sm text-arch-ink/80">
              Для разных ракурсов используется отдельная разметка панелей, чтобы не притворяться,
              что фотографии можно идеально наложить.
            </p>
          </div>
        </div>
        <p className="mt-4 text-sm text-arch-muted">
          Если сайту не хватает метаданных для безопасного наложения, он не должен показывать
          интерактивный слой вместо того, чтобы рисовать неверную подсветку.
        </p>
      </MethodSection>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <MethodSection title="Честные границы прототипа" kicker="Что уже работает и что демо">
          <ul className="list-inside list-disc space-y-2 text-sm leading-relaxed text-arch-ink/80">
            {LIMITS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </MethodSection>

        <MethodSection title="Что показывать на презентации" kicker="Демо-маршрут">
          <div className="space-y-3">
            {DEMO_CASES.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="block rounded-xl border border-arch-line bg-arch-surface-2/40 p-4 transition hover:border-arch-green/40 hover:bg-arch-green-soft"
              >
                <h3 className="font-semibold text-arch-green-deep">{item.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-arch-ink/75">{item.text}</p>
              </Link>
            ))}
          </div>
        </MethodSection>
      </div>

      <MethodSection title="Слайд, который можно почти сразу перенести в презентацию" kicker="Коротко">
        <div className="rounded-xl border border-arch-green/25 bg-arch-green-soft p-5">
          <p className="text-base font-semibold text-arch-green-deep">
            Archiview готовит доказательную визуальную основу, сайт превращает её в понятный
            публичный рассказ.
          </p>
          <p className="mt-3 text-sm leading-relaxed text-arch-ink/80">
            Техническая ценность проекта в том, что фасад становится интерфейсом: пользователь видит
            конкретную зону на фотографии, читает интерпретацию, проверяет источник и понимает, как
            слой прошлого связан с сегодняшним обликом здания.
          </p>
        </div>
      </MethodSection>
    </div>
  )
}
