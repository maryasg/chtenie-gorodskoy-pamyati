import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { PILOT_TOUR } from '../data/tour'

export function TourPage() {
  const [step, setStep] = useState(0)
  const current = PILOT_TOUR[step]
  const building = getBuildingById(current.buildingId)

  return (
    <div className="space-y-6">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <p className="arch-kicker mb-1">Маршрут пилота</p>
        <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">Готовая экскурсия</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-arch-muted">
          Четыре точки складываются в короткий сценарий чтения фасадов: от слоёв модерна до
          вывесок, палат и современной надстройки.
        </p>
      </header>

      <p className="text-sm text-arch-muted">
        Маршрут по четырём проверенным зданиям пилота. Шаг {step + 1} из {PILOT_TOUR.length}.
      </p>

      <div className="arch-section">
        <p className="arch-kicker">
          Точка {step + 1}
        </p>
        <h2 className="mt-1 text-xl font-semibold text-arch-green-deep">{current.title}</h2>
        <p className="mt-3 text-sm leading-relaxed text-arch-ink/80">{current.methodologyNote}</p>
        {building && (
          <p className="mt-2 text-sm text-arch-muted">{building.address}</p>
        )}
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={step === 0}
            onClick={() => setStep((s) => s - 1)}
            className="rounded-full border border-arch-line bg-arch-surface px-4 py-2 text-sm font-medium text-arch-green-deep transition hover:border-arch-green/40 hover:bg-arch-green-soft disabled:opacity-40"
          >
            Назад
          </button>
          {step < PILOT_TOUR.length - 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="rounded-full bg-arch-green-deep px-4 py-2 text-sm font-medium text-arch-surface transition hover:bg-arch-green"
            >
              Далее
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setStep(0)}
              className="rounded-full bg-arch-green-deep px-4 py-2 text-sm font-medium text-arch-surface transition hover:bg-arch-green"
            >
              Сначала
            </button>
          )}
          {building && (
            <Link
              to={`/building/${building.id}`}
              className="rounded-full border border-arch-green/40 bg-arch-green-soft px-4 py-2 text-sm font-medium text-arch-green-deep transition hover:bg-arch-surface"
            >
              Открыть карточку
            </Link>
          )}
        </div>
      </div>

      <ol className="mt-6 flex flex-wrap gap-2">
        {PILOT_TOUR.map((t, i) => (
          <li key={t.buildingId}>
            <button
              type="button"
              onClick={() => setStep(i)}
              className={`rounded-full px-3 py-1 text-xs ${
                i === step
                  ? 'bg-arch-green-deep text-arch-surface'
                  : 'border border-arch-line bg-arch-surface text-arch-muted hover:bg-arch-green-soft hover:text-arch-green-deep'
              }`}
            >
              {i + 1}. {t.title}
            </button>
          </li>
        ))}
      </ol>
    </div>
  )
}
