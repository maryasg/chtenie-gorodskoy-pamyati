import { Link, useParams } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import { FacadeHotspotViewer } from '../components/FacadeHotspotViewer'
import { TransformationTimeline } from '../components/TransformationTimeline'

export function BuildingPage() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined

  if (!building) {
    return (
      <p>
        Здание не найдено. <Link to="/">На карту</Link>
      </p>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <Link to="/" className="text-sm text-stone-500 hover:text-stone-800">
          ← Карта
        </Link>
        <div className="mt-2 flex flex-wrap items-start gap-2">
          <h1 className="text-2xl font-semibold">{building.name}</h1>
          {building.cardStatus === 'pilot_in_progress' && (
            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800">
              Пилот v{building.cardVersion ?? '0.1'}
            </span>
          )}
        </div>
        <p className="text-stone-600">{building.address}</p>
        <p className="mt-2 text-sm text-stone-700">{building.headline}</p>
        <div className="mt-2 flex flex-wrap gap-2 text-sm text-stone-500">
          <span>{building.style}</span>
          <span>·</span>
          <span>{building.yearBuilt}</span>
          {building.architect && (
            <>
              <span>·</span>
              <span>{building.architect}</span>
            </>
          )}
        </div>
      </div>

      <section>
        <h2 className="mb-2 text-lg font-semibold">Интерпретация</h2>
        <p className="text-sm leading-relaxed text-stone-700">{building.summary}</p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Фасад и подсветка</h2>
        <FacadeHotspotViewer building={building} />
        <Link
          to={`/building/${building.id}/ar`}
          className="mt-3 inline-block text-sm font-medium text-stone-800 underline"
        >
          Симуляция AR-preview →
        </Link>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Этапы трансформации</h2>
        <TransformationTimeline stages={building.timeline} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Следы памяти</h2>
        <ul className="space-y-4">
          {building.memoryTraces.map((t) => (
            <li key={t.id} className="rounded-lg border border-stone-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-medium">{t.title}</h3>
                <ConfidenceBadge level={t.confidence} />
                <span className="text-xs text-stone-500">{t.period}</span>
              </div>
              <p className="mt-2 text-sm text-stone-700">{t.userMessage}</p>
            </li>
          ))}
        </ul>
      </section>

      {building.artifacts.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Сохранившиеся артефакты</h2>
          <ul className="space-y-2">
            {building.artifacts.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">{a.title}</span>
                <ConfidenceBadge level={a.confidence} />
                <span className="text-stone-500">{a.period}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold">Визуальные материалы</h2>
        <ul className="space-y-2 text-sm">
          {building.photos.map((p) => (
            <li key={p.id}>
              {p.url ? (
                <a href={p.url} target="_blank" rel="noreferrer" className="text-blue-700 underline">
                  {p.description}
                </a>
              ) : (
                <span>
                  {p.description}
                  {p.status ? ` (${p.status})` : ''}
                </span>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-2 text-lg font-semibold">Источники</h2>
        <ul className="list-inside list-disc text-sm text-stone-700">
          {building.sources.map((s) => (
            <li key={s.id}>
              {s.url ? (
                <a href={s.url} target="_blank" rel="noreferrer" className="underline">
                  {s.name}
                </a>
              ) : (
                s.name
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
