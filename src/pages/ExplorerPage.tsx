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
    <div className="max-w-2xl space-y-6">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <p className="arch-kicker mb-1">Демо-сценарий</p>
        <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">Режим исследователя</h1>
        <p className="mt-2 text-sm leading-relaxed text-arch-muted">
          Имитация рабочего процесса <strong>Archiview</strong>: загрузка фото → первичное чтение →
          гипотезы. Готовая разметка с номерами областей — в{' '}
          <Link to={`/building/${PILOT.buildingId}`} className="font-medium text-arch-green underline">
            карточке здания
          </Link>{' '}
          (пилот: дом со зверями).
        </p>
      </header>

      <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
        <p className="text-sm font-semibold text-amber-950">
          Демо-режим: здесь показан сценарий будущей функции. Реальная разметка и проверка следов
          выполняются куратором в Archiview.
        </p>
      </div>

      <ol className="flex flex-wrap gap-2 text-xs font-medium text-arch-muted">
        {([1, 2, 3] as const).map((n) => (
          <li
            key={n}
            className={`rounded-full px-3 py-1 ${
              step >= n
                ? 'bg-arch-green-deep text-arch-surface'
                : 'border border-arch-line bg-arch-surface text-arch-muted'
            }`}
          >
            {n === 1 ? 'Фото' : n === 2 ? 'Подсказки' : 'Чтение'}
          </li>
        ))}
      </ol>

      <section className="arch-section">
        <h2 className="mb-2 text-sm font-semibold text-arch-green-deep">1. Загрузите фото фасада</h2>
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
          className="mb-2 block w-full text-sm text-arch-ink file:mr-3 file:rounded-full file:border-0 file:bg-arch-green-deep file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-arch-surface"
        />
        {file && (
          <p className="text-xs text-arch-muted">
            Выбрано: {file.name} · далее — «Запустить чтение фасада»
          </p>
        )}
      </section>

      <section className="arch-section">
        <h2 className="mb-2 text-sm font-semibold text-arch-green-deep">2. Подсказки съёмки</h2>
        <ul className="list-inside list-disc text-sm leading-relaxed text-arch-ink/80">
          {TIPS.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      </section>

      <section className="arch-section">
        <h2 className="mb-3 text-sm font-semibold text-arch-green-deep">3. Запустить чтение фасада</h2>
        <button
          type="button"
          disabled={!file || analyzing}
          onClick={runMock}
          className="rounded-full bg-arch-green-deep px-4 py-2 text-sm font-medium text-arch-surface transition hover:bg-arch-green disabled:opacity-50"
        >
          {analyzing ? 'Анализ фасада…' : 'Запустить чтение фасада (demo)'}
        </button>
        <p className="mt-2 text-xs text-arch-muted">
          В программе Archiview на ПК — те же шаги с выпрямлением, сравнением и разметкой.
        </p>
      </section>

      {done && (
        <div className="arch-section space-y-4">
          <p className="text-sm font-medium text-arch-green-deep">Найденные следы (демо-гипотезы)</p>
          {MOCK_TRACES.map((tr) => (
            <div key={tr.title}>
              <p className="font-medium">{tr.title}</p>
              <ConfidenceBadge level="needs_verification" />
              <ul className="mt-2 space-y-1 text-sm text-arch-ink/80">
                {tr.hypotheses.map((h) => (
                  <li key={h.label}>
                    {h.label} — {h.weight}%
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <p className="text-sm text-arch-muted">
            Итог с подсветкой областей и номерами на фото смотрите в{' '}
            <Link to={`/building/${PILOT.buildingId}`} className="font-medium text-arch-green underline">
              карточке «Дом со зверями»
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  )
}
