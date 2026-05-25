import { useState } from 'react'
import { ConfidenceBadge } from '../components/ConfidenceBadge'

const TIPS = [
  'Снимайте общий план фасада целиком',
  'Держите камеру без сильного наклона',
  'Достаточное освещение, объект в кадре',
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

export function ExplorerPage() {
  const [file, setFile] = useState<File | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [done, setDone] = useState(false)

  const runMock = () => {
    if (!file) return
    setAnalyzing(true)
    setDone(false)
    setTimeout(() => {
      setAnalyzing(false)
      setDone(true)
    }, 1500)
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-2 text-2xl font-semibold">Режим исследователя</h1>
      <p className="mb-4 text-sm text-stone-600">
        Загрузите фото фасада неподготовленного здания. В пилоте анализ имитируется — без реального
        AI/CV.
      </p>

      <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4">
        <p className="text-sm font-semibold text-amber-900">
          Первичное AI-чтение · проверка куратором не проводилась
        </p>
      </div>

      <h2 className="mb-2 text-sm font-semibold">Подсказки съёмки</h2>
      <ul className="mb-4 list-inside list-disc text-sm text-stone-700">
        {TIPS.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>

      <input
        type="file"
        accept="image/*"
        capture="environment"
        onChange={(e) => {
          setFile(e.target.files?.[0] ?? null)
          setDone(false)
        }}
        className="mb-4 block w-full text-sm"
      />

      {file && (
        <p className="mb-2 text-xs text-stone-500">Выбрано: {file.name}</p>
      )}

      <button
        type="button"
        disabled={!file || analyzing}
        onClick={runMock}
        className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {analyzing ? 'Анализ…' : 'Запустить чтение фасада (demo)'}
      </button>

      {done && (
        <div className="mt-6 space-y-4 rounded-xl border border-stone-200 bg-white p-4">
          <p className="text-sm font-medium">Найденные следы (mock)</p>
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
          <p className="text-xs text-stone-500">
            В полной версии: Roboflow + OpenCV → Trace Detector → Confidence Engine.
          </p>
        </div>
      )}
    </div>
  )
}
