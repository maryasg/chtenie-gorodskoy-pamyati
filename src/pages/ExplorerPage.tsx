import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import {
  MOSCOW_003_EXPLORER,
  type ArchiviewAnnotation,
} from '../data/explorer/moscow003Archiview'

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
  const [pilotAnnotations, setPilotAnnotations] = useState<ArchiviewAnnotation[]>([])
  const [pilotImageOk, setPilotImageOk] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetch(MOSCOW_003_EXPLORER.annotationsUrl)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (cancelled || !data?.annotations) return
        setPilotAnnotations(data.annotations as ArchiviewAnnotation[])
      })
      .catch(() => {})
    const img = new Image()
    img.onload = () => {
      if (!cancelled) setPilotImageOk(true)
    }
    img.onerror = () => {
      if (!cancelled) setPilotImageOk(false)
    }
    img.src = MOSCOW_003_EXPLORER.markedFacadeUrl
    return () => {
      cancelled = true
    }
  }, [])

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
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="mb-2 text-2xl font-semibold">Режим исследователя</h1>
        <p className="text-sm text-stone-600">
          Загрузите фото фасада или откройте готовое чтение пилотного здания (Archiview).
        </p>
      </div>

      <section className="rounded-xl border border-stone-200 bg-white p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold">{MOSCOW_003_EXPLORER.title}</h2>
          <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-900">
            Пилот Archiview
          </span>
        </div>
        <p className="mb-3 text-sm text-stone-600">
          Эталон пилота: сравнение исторического и современного фасада, разметка изменений.
          На карте —{' '}
          <Link
            to={`/building/${MOSCOW_003_EXPLORER.buildingId}`}
            className="font-medium text-stone-800 underline"
          >
            карточка здания
          </Link>
          .
        </p>

        {pilotImageOk ? (
          <a
            href={MOSCOW_003_EXPLORER.markedFacadeUrl}
            target="_blank"
            rel="noreferrer"
            className="mb-3 block"
          >
            <img
              src={MOSCOW_003_EXPLORER.markedFacadeUrl}
              alt="Разметка фасада Archiview, Чистопрудный 14с3"
              className="max-h-[min(70vh,720px)] w-full rounded-lg border border-stone-200 object-contain"
            />
          </a>
        ) : (
          <p className="mb-3 rounded-lg border border-dashed border-stone-300 bg-stone-50 p-4 text-sm text-stone-600">
            Картинка с номерами областей пока не на сайте. В Archiview v15 сохраните разметку, запустите{' '}
            <code className="text-xs">copy_to_website.bat</code>, затем Push в GitHub Desktop.
          </p>
        )}

        {pilotAnnotations.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold">Области ({pilotAnnotations.length})</h3>
            <ul className="max-h-64 space-y-2 overflow-y-auto text-sm text-stone-700">
              {pilotAnnotations.map((ann, i) => (
                <li key={ann.id ?? i} className="rounded border border-stone-100 bg-stone-50 px-3 py-2">
                  <span className="font-medium">
                    {i + 1}. {ann.label_ru || ann.class}
                  </span>
                  {ann.comment ? (
                    <p className="mt-1 text-stone-600">Комментарий: {ann.comment}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        )}

        <ConfidenceBadge level="needs_verification" />
      </section>

      <section className="max-w-xl">
        <h2 className="mb-2 text-lg font-semibold">Другое здание (демо)</h2>
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-900">
            Первичное AI-чтение · проверка куратором не проводилась
          </p>
        </div>

        <h3 className="mb-2 text-sm font-semibold">Подсказки съёмки</h3>
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

        {file && <p className="mb-2 text-xs text-stone-500">Выбрано: {file.name}</p>}

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
          </div>
        )}
      </section>
    </div>
  )
}
