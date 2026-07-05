import { Link } from 'react-router-dom'
import { BUILDINGS } from '../../data/buildings'
import { V2Plate, V2Manifest } from '../components/V2Plate'
import { V2SquareMark } from '../components/V2SquareMark'

const METHOD_STEPS = [
  {
    num: '01',
    code: 'SCN',
    title: 'Собрать пару',
    text: 'Историческое и современное фото одного фасада — с понятной плоскостью и опорными точками.',
  },
  {
    num: '02',
    code: 'MRK',
    title: 'Разметить в Archiview',
    text: 'Overlay или side-by-side: зоны надстроек, утрат декора, вывесок и мемориальных слоёв.',
  },
  {
    num: '03',
    code: 'RD',
    title: 'Читать на сайте',
    text: 'Карта, карточка здания, экскурсия и режим исследователя — с уровнями уверенности.',
  },
]

const CAPABILITIES = [
  { code: 'MAP', title: 'Карта пилотных объектов', meta: '4 BUILDINGS' },
  { code: 'TRC', title: 'Следы памяти с уровнем уверенности', meta: 'CONFIDENCE TIERS' },
  { code: 'ARX', title: 'Archiview overlay и сравнения', meta: 'MULTI-LAYER' },
  { code: 'EXP', title: 'Экспертная разметка и экспорт', meta: 'SITE SYNC' },
  { code: 'SIM', title: 'Исследователь и AR-симуляция', meta: 'PREVIEW' },
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
            <p className="v2-kicker">MVP · pilot · 4 objects</p>
            <h1 className="v2-hero-title mt-4 text-v2-ink">
              Читать невидимое
              <br />
              на фасаде
            </h1>
            <p className="mt-6 max-w-xl text-sm leading-relaxed text-v2-muted normal-case sm:text-base">
              Платформа для чтения городской памяти: исторические слои, экспертная разметка и
              интерактивные карточки зданий.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link to="/v2/map" className="v2-btn-primary">
                Открыть карту
              </Link>
              <a href="#method" className="v2-btn-text">
                Метод →
              </a>
            </div>
          </div>

          <figure className="v2-panel overflow-hidden">
            <img
              src={facadeImage('MOSCOW_003')}
              alt="Размеченный фасад — дом со зверями"
              className="aspect-[4/3] w-full object-cover"
            />
            <figcaption className="border-t border-v2-line px-4 py-3 sm:px-5">
              <p className="v2-kicker">FIG · MOSCOW_003</p>
              <p className="v2-mono-xs mt-1 text-v2-muted normal-case">
                Чистопрудный 14с3 · эталон пилота
              </p>
            </figcaption>
          </figure>
        </div>
      </section>

      <section id="method" className="border-y border-v2-line bg-v2-surface py-16 sm:py-20">
        <div className="v2-container">
          <V2Manifest kicker="Methodology" title="Метод" count="3 STEPS">
            {METHOD_STEPS.map((step, index) => (
              <V2Plate
                key={step.num}
                code={step.code}
                title={step.title}
                description={step.text}
                meta={`STEP ${step.num}`}
                active={index === 0}
              />
            ))}
          </V2Manifest>
        </div>
      </section>

      <section id="objects" className="v2-container py-16 sm:py-20">
        <V2Manifest kicker="Archive" title="Пилотные объекты" count={`${BUILDINGS.length} CARDS`}>
          {BUILDINGS.map((building, index) => {
            const img = building.cardId ? facadeImage(building.cardId) : undefined
            return (
              <div key={building.id} className="v2-plate-row">
                <Link to={`/v2/building/${building.id}`} className="group block">
                  <div className="flex gap-3">
                    <div className="pt-0.5">
                      <V2SquareMark active={index === 0} innerColor="#64748b" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <h3 className="v2-mono-sm font-semibold text-v2-ink group-hover:text-v2-red">
                          {building.cardId ?? building.id}
                        </h3>
                        <span className="v2-btn-text opacity-0 transition group-hover:opacity-100">
                          Открыть →
                        </span>
                      </div>
                      <p className="v2-display mt-1 text-lg text-v2-ink normal-case">{building.name}</p>
                      <p className="v2-mono-xs mt-1 text-v2-muted normal-case">{building.address}</p>
                      {img ? (
                        <img
                          src={img}
                          alt=""
                          className="mt-3 aspect-[16/7] w-full border border-v2-line object-cover"
                        />
                      ) : null}
                    </div>
                  </div>
                </Link>
              </div>
            )
          })}
        </V2Manifest>
      </section>

      <section className="border-y border-v2-line bg-v2-surface py-16 sm:py-20">
        <div className="v2-container">
          <V2Manifest kicker="System" title="Возможности" count={`${CAPABILITIES.length} MODULES`}>
            {CAPABILITIES.map((item, index) => (
              <V2Plate
                key={item.code}
                code={item.code}
                title={item.title}
                meta={item.meta}
                active={index === 0}
                markColor={index === 0 ? '#d63f46' : '#9ca3af'}
              />
            ))}
          </V2Manifest>
        </div>
      </section>

      <section className="bg-v2-footer py-16 text-white sm:py-20">
        <div className="v2-container flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="v2-kicker text-v2-red">Preview branch</p>
            <p className="v2-display mt-3 max-w-lg text-2xl leading-snug sm:text-3xl">
              Новый интерфейс без изменения боевого сайта
            </p>
            <p className="mt-4 max-w-md text-sm text-white/65 normal-case">
              Версия <code className="text-white/90">/v2/</code> в отдельной ветке. Основной сайт на{' '}
              <code className="text-white/90">/</code> не меняется.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link to="/v2/map" className="v2-btn-primary border-white bg-white text-v2-ink">
              Смотреть карту
            </Link>
            <Link to="/" className="v2-btn-text text-white/80 hover:opacity-100">
              Старый сайт →
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
