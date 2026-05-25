import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { PILOT_TOUR } from '../data/tour'

export function TourPage() {
  const [step, setStep] = useState(0)
  const current = PILOT_TOUR[step]
  const building = getBuildingById(current.buildingId)

  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold">Готовая экскурсия</h1>
      <p className="mb-6 text-sm text-stone-600">
        Маршрут по четырём проверенным зданиям пилота. Шаг {step + 1} из {PILOT_TOUR.length}.
      </p>

      <div className="rounded-xl border border-stone-200 bg-white p-6">
        <p className="text-xs font-medium uppercase tracking-wide text-stone-500">
          Точка {step + 1}
        </p>
        <h2 className="mt-1 text-xl font-semibold">{current.title}</h2>
        <p className="mt-3 text-sm text-stone-700">{current.methodologyNote}</p>
        {building && (
          <p className="mt-2 text-sm text-stone-500">{building.address}</p>
        )}
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={step === 0}
            onClick={() => setStep((s) => s - 1)}
            className="rounded-lg border border-stone-300 px-4 py-2 text-sm disabled:opacity-40"
          >
            Назад
          </button>
          {step < PILOT_TOUR.length - 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white"
            >
              Далее
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setStep(0)}
              className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white"
            >
              Сначала
            </button>
          )}
          {building && (
            <Link
              to={`/building/${building.id}`}
              className="rounded-lg border border-stone-900 px-4 py-2 text-sm font-medium"
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
                i === step ? 'bg-stone-900 text-white' : 'bg-stone-200 text-stone-700'
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
