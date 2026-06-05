import { Link, useParams } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import { ArchiviewFacadePanel } from '../components/ArchiviewFacadePanel'
import { BuildingVerificationBanner } from '../components/BuildingVerificationBanner'
import { FacadeBeforeAfterSlider } from '../components/FacadeBeforeAfterSlider'
import { FacadeHotspotViewer } from '../components/FacadeHotspotViewer'
import { TransformationTimeline } from '../components/TransformationTimeline'
import { getArchiviewAssets } from '../data/explorer/archiviewAssets'

import type { ReactNode } from 'react'

function Section({
  title,
  kicker,
  children,
  className = '',
}: {
  title: string
  kicker?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`arch-section ${className}`}>
      {kicker ? <p className="arch-kicker mb-1">{kicker}</p> : null}
      <h2 className="arch-section-title mb-3">{title}</h2>
      {children}
    </section>
  )
}

export function BuildingPage() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined
  const archiview = building ? getArchiviewAssets(building.id) : undefined

  if (!building) {
    return (
      <p className="text-arch-muted">
        Здание не найдено. <Link to="/" className="font-medium text-arch-green underline">На карту</Link>
      </p>
    )
  }

  return (
    <div className="space-y-6">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <Link
          to="/"
          className="text-sm font-medium text-arch-green-light hover:text-arch-green-deep"
        >
          ← Карта пилота
        </Link>
        <div className="mt-3 flex flex-wrap items-start gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">{building.name}</h1>
          {building.cardStatus === 'pilot_in_progress' && (
            <span className="arch-pill border-arch-green/30 bg-arch-green-soft text-arch-green">
              Пилот v{building.cardVersion ?? '0.1'}
            </span>
          )}
        </div>
        <p className="mt-1 text-arch-muted">{building.address}</p>
        <p className="mt-3 text-sm leading-relaxed text-arch-ink/90">{building.headline}</p>
        <div className="mt-3 flex flex-wrap gap-2 text-sm text-arch-muted">
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
      </header>

      {building.verification && <BuildingVerificationBanner verification={building.verification} />}

      <Section title="Интерпретация" kicker="Карточка здания">
        <p className="text-sm leading-relaxed text-arch-ink/85">{building.summary}</p>
      </Section>

      {archiview ? (
        <Section title="Фасад и подсветка" kicker="Archiview">
          <ArchiviewFacadePanel assets={archiview} />
        </Section>
      ) : (
        <Section title="Фасад и подсветка">
          <FacadeHotspotViewer building={building} />
          <Link
            to={`/building/${building.id}/ar`}
            className="mt-3 inline-block text-sm font-medium text-arch-green underline"
          >
            Симуляция AR-preview →
          </Link>
        </Section>
      )}

      <Section title="Следы памяти">
        <ul className="space-y-3">
          {building.memoryTraces.map((t) => (
            <li
              key={t.id}
              className="rounded-xl border border-arch-line bg-arch-surface-2/50 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-medium text-arch-ink">{t.title}</h3>
                <ConfidenceBadge level={t.confidence} />
                <span className="text-xs text-arch-muted">{t.period}</span>
              </div>
              <p className="mt-2 text-sm text-arch-ink/80">{t.userMessage}</p>
            </li>
          ))}
        </ul>
      </Section>

      {archiview ? (
        <>
          <Section title="Две реальности" kicker="История ↔ сегодня">
            <FacadeBeforeAfterSlider
              historicalUrl={archiview.historicalRectifiedUrl}
              modernUrl={archiview.modernRectifiedUrl}
              historicalYear={archiview.historicalPhotoYear}
              modernYear={archiview.modernPhotoYear}
            />
          </Section>
          <p>
            <Link
              to={`/building/${building.id}/ar`}
              className="inline-flex items-center gap-1 rounded-full border border-arch-line bg-arch-surface px-4 py-2 text-sm font-medium text-arch-green-deep hover:border-arch-green/40 hover:bg-arch-green-soft"
            >
              AR-preview: слои времени на фасаде →
            </Link>
          </p>
        </>
      ) : null}

      <Section title="Этапы трансформации">
        <TransformationTimeline stages={building.timeline} />
      </Section>

      {building.artifacts.length > 0 && (
        <Section title="Сохранившиеся артефакты">
          <ul className="space-y-2">
            {building.artifacts.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">{a.title}</span>
                <ConfidenceBadge level={a.confidence} />
                <span className="text-arch-muted">{a.period}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Визуальные материалы">
        <ul className="space-y-2 text-sm">
          {building.photos.map((p) => (
            <li key={p.id}>
              {p.url ? (
                <a
                  href={p.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-arch-green underline decoration-arch-green/30"
                >
                  {p.description}
                </a>
              ) : (
                <span className="text-arch-muted">
                  {p.description}
                  {p.status ? ` (${p.status})` : ''}
                </span>
              )}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Источники">
        <ul className="list-inside list-disc space-y-1 text-sm text-arch-ink/80">
          {building.sources.map((s) => (
            <li key={s.id}>
              {s.url ? (
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-arch-green underline"
                >
                  {s.name}
                </a>
              ) : (
                s.name
              )}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  )
}
