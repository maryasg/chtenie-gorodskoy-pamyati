import { Link } from 'react-router-dom'
import { BUILDINGS } from '../../data/buildings'

const METHOD_STEPS = [
  {
    num: '01',
    title: 'Собрать пару',
    text: 'Историческое и современное фото одного фасада — с понятной плоскостью и опорными точками.',
  },
  {
    num: '02',
    title: 'Разметить в Archiview',
    text: 'Overlay или side-by-side: зоны надстроек, утрат декора, вывесок и мемориальных слоёв.',
  },
  {
    num: '03',
    title: 'Читать на сайте',
    text: 'Карта, карточка здания, экскурсия и режим исследователя — с уровнями уверенности.',
  },
]

const CAPABILITIES = [
  'Карта пилотных объектов Москвы',
  'Следы памяти с уровнем уверенности',
  'Archiview: overlay и сравнения',
  'Экспертная разметка и экспорт на сайт',
  'Режим исследователя и AR-симуляция',
]

const FACADE_IMAGES: Record<string, string> = {
  MOSCOW_001: 'explorer/MOSCOW_001/comparisons/cmp_005/marked-facade.png',
  MOSCOW_002: 'explorer/MOSCOW_002/marked-facade.png',
  MOSCOW_003: 'explorer/MOSCOW_003/marked-facade.png',
  MOSCOW_004: 'explorer/MOSCOW_004/marked-facade-labeled.png',
}

function facadeImage(cardId: string) {
  const rel = FACADE_IMAGES[cardId]
  return rel ? `${import.meta.env.BASE_URL}${rel}` : undefined
}

export function HomeV2() {
  return (
    <div>
      <section className="v2-container py-16 sm:py-24">
        <div className="grid items-end gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="v2-kicker">MVP · пилот · 4 объекта</p>
            <h1 className="v2-hero-title mt-4 text-v2-ink">
              Читать невидимое
              <br />
              <em>на фасаде</em>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-v2-muted sm:text-lg">
              Платформа для чтения городской памяти: исторические слои, экспертная разметка и
              интерактивные карточки зданий — от карты до режима исследователя.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/v2/map" className="v2-btn-primary">
                Открыть карту
              </Link>
              <a href="#method" className="v2-btn-outline">
                Как устроен метод
              </a>
            </div>
          </div>

          <div className="v2-card overflow-hidden p-0">
            <img
              src={facadeImage('MOSCOW_003')}
              alt="Размеченный фасад — дом со зверями"
              className="aspect-[4/3] w-full object-cover"
            />
            <div className="border-t border-v2-line px-5 py-4">
              <p className="v2-kicker">REF. MOSCOW_003</p>
              <p className="mt-1 text-sm font-medium">Чистопрудный 14с3 · эталон пилота</p>
            </div>
          </div>
        </div>
      </section>

      <section id="method" className="border-y border-v2-line bg-v2-surface py-16 sm:py-20">
        <div className="v2-container">
          <p className="v2-kicker">Methodology</p>
          <h2 className="v2-section-title mt-2">Метод</h2>
          <div className="mt-10 grid gap-8 md:grid-cols-3">
            {METHOD_STEPS.map((step) => (
              <article key={step.num} className="border-t border-v2-line pt-6">
                <p className="text-xs font-bold tracking-[0.2em] text-v2-muted">{step.num}</p>
                <h3 className="mt-3 text-sm font-bold tracking-[0.12em] uppercase">{step.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-v2-muted">{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="objects" className="v2-container py-16 sm:py-20">
        <p className="v2-kicker">Archive</p>
        <h2 className="v2-section-title mt-2">Пилотные объекты</h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {BUILDINGS.map((building) => {
            const img = building.cardId ? facadeImage(building.cardId) : undefined
            return (
              <Link
                key={building.id}
                to={`/v2/building/${building.id}`}
                className="v2-card group overflow-hidden transition hover:shadow-md"
              >
                {img ? (
                  <img
                    src={img}
                    alt=""
                    className="aspect-[16/10] w-full object-cover transition group-hover:scale-[1.01]"
                  />
                ) : (
                  <div className="aspect-[16/10] bg-v2-surface-muted" />
                )}
                <div className="p-5">
                  <p className="v2-kicker">{building.cardId}</p>
                  <h3 className="mt-1 text-base font-semibold leading-snug">{building.name}</h3>
                  <p className="mt-2 text-sm text-v2-muted">{building.address}</p>
                </div>
              </Link>
            )
          })}
        </div>
      </section>

      <section className="border-y border-v2-line bg-v2-surface py-16 sm:py-20">
        <div className="v2-container grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="v2-kicker">System capabilities</p>
            <h2 className="v2-section-title mt-2">Возможности</h2>
          </div>
          <ul className="space-y-4">
            {CAPABILITIES.map((item) => (
              <li
                key={item}
                className="flex items-start gap-3 border-b border-v2-line pb-4 text-sm text-v2-muted last:border-0"
              >
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-v2-red" aria-hidden />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="bg-v2-footer py-16 text-white sm:py-20">
        <div className="v2-container flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="v2-kicker text-v2-red">Preview branch</p>
            <p className="mt-3 max-w-lg text-2xl leading-snug font-medium sm:text-3xl">
              Новый интерфейс — без изменения боевого сайта
            </p>
            <p className="mt-4 max-w-md text-sm text-white/65">
              Это версия <code className="text-white/90">/v2/</code> в отдельной ветке. Основной
              сайт остаётся на <code className="text-white/90">/</code>, пока вы не решите слить PR.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/v2/map" className="v2-btn-primary">
              Смотреть карту
            </Link>
            <Link to="/" className="v2-btn-outline border-white/20 bg-transparent text-white hover:bg-white/10">
              Сравнить со старым
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
