import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import { ARCHIVIEW_ASSETS } from '../data/explorer/archiviewAssets'

const TIPS = [
  'Снимайте общий план фасада целиком',
  'Держите камеру без сильного наклона',
  'Достаточное освещение, объект в кадре',
  'Четыре угла — одна плоскость фасада (как в Archiview)',
]

const MOCK_TRACES = [
  {
    title: 'Прямоугольная зона с иной фактурой',
    hypotheses: [
      { label: 'Заложенное окно', weight: 75 },
      { label: 'Декоративная ниша', weight: 15 },
      { label: 'Закрашенное окно', weight: 10 },
    ],
  },
]

const PILOT = ARCHIVIEW_ASSETS.MOSCOW_003_dom_so_zveryami

export function ExplorerPage() {
  const [file, setFile] = useState<File | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [done, setDone] = useState(false)
  const [step, setStep] = useState<1 | 2 | 3>(1)

  const runMock = () => {
    if (!file) return
    setAnalyzing(true)
    setDone(false)
    setStep(3)
    setTimeout(() => {
      setAnalyzing(false)
      setDone(true)
    }, 2000)
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="mb-2 text-2xl font-semibold">Режим исследователя</h1>
        <p className="text-sm text-stone-600">
          Имитация рабочего процесса <strong>Archiview</strong>: загрузка фото → первичное чтение →
          гипотезы. Готовая разметка с номерами областей — в{' '}
          <Link to={`/building/${PILOT.buildingId}`} className="font-medium underline">
            карточке здания
          </Link>{' '}
          (пилот: дом со зверями).
        </p>
      </div>

      <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
        <p className="text-sm font-semibold text-amber-900">
          Первичное AI-чтение · проверка куратором не проводилась
        </p>
      </div>

      <ol className="flex flex-wrap gap-2 text-xs font-medium text-stone-600">
        {([1, 2, 3] as const).map((n) => (
          <li
            key={n}
            className={`rounded-full px-3 py-1 ${
              step >= n ? 'bg-stone-900 text-white' : 'bg-stone-200 text-stone-600'
            }`}
          >
            {n === 1 ? 'Фото' : n === 2 ? 'Подсказки' : 'Чтение'}
          </li>
        ))}
      </ol>

      <section className="rounded-xl border border-stone-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-semibold">1. Загрузите фото фасада</h2>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => {
            const f = e.target.files?.[0] ?? null
            setFile(f)
            setDone(false)
            if (f) setStep(2)
          }}
          className="mb-2 block w-full text-sm"
        />
        {file && (
          <p className="text-xs text-stone-500">
            Выбрано: {file.name} · далее — «Запустить чтение фасада»
          </p>
        )}
      </section>

      <section className="rounded-xl border border-stone-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-semibold">2. Подсказки съёмки (как в Archiview)</h2>
        <ul className="list-inside list-disc text-sm text-stone-700">
          {TIPS.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-stone-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold">3. Запустить чтение фасада</h2>
        <button
          type="button"
          disabled={!file || analyzing}
          onClick={runMock}
          className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {analyzing ? 'Анализ фасада…' : 'Запустить чтение фасада (demo)'}
        </button>
        <p className="mt-2 text-xs text-stone-500">
          В программе Archiview на ПК — те же шаги с выпрямлением, сравнением и разметкой.
        </p>
      </section>

      {done && (
        <div className="space-y-4 rounded-xl border border-stone-200 bg-white p-4">
          <p className="text-sm font-medium">Найденные следы (демо-гипотезы)</p>
          {MOCK_TRACES.map((tr) => (
            <div key={tr.title}>
              <p className="font-medium">{tr.title}</p>
              <ConfidenceBadge level="needs_verification" />
              <ul className="mt-2 space-y-1 text-sm text-stone-700">
                {tr.hypotheses.map((h) => (
                  <li key={h.label}>
                    {h.label} — {h.weight}%
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <p className="text-sm text-stone-600">
            Итог с подсветкой областей и номерами на фото смотрите в{' '}
            <Link to={`/building/${PILOT.buildingId}`} className="font-medium underline">
              карточке «Дом со зверями»
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  )
}
