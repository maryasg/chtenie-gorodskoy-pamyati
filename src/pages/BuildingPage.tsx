import { Link, useParams } from 'react-router-dom'
import { getBuildingById } from '../data/buildings'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import { ArchiviewFacadePanel } from '../components/ArchiviewFacadePanel'
import { BuildingVerificationBanner } from '../components/BuildingVerificationBanner'
import { FacadeBeforeAfterSlider } from '../components/FacadeBeforeAfterSlider'
import { FacadeHotspotViewer } from '../components/FacadeHotspotViewer'
import { TransformationTimeline } from '../components/TransformationTimeline'
import { getArchiviewAssets } from '../data/explorer/archiviewAssets'

import { useState, type ReactNode } from 'react'
import type { Building, MemoryTrace } from '../types/building'
import type { ArchiviewBuildingAssets } from '../data/explorer/archiviewAssets'

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

function publicAssetUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path
  return `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`
}

function MemoryTraceImage({ trace }: { trace: MemoryTrace }) {
  const [hidden, setHidden] = useState(false)
  if (!trace.imagePath || hidden) return null

  return (
    <figure className="mt-3 overflow-hidden rounded-xl border border-arch-line bg-arch-surface">
      <img
        src={publicAssetUrl(trace.imagePath)}
        alt={trace.imageCaption ?? trace.title}
        loading="lazy"
        onError={() => setHidden(true)}
        className="max-h-72 w-full object-cover"
      />
      {trace.imageCaption && (
        <figcaption className="px-3 py-2 text-xs leading-relaxed text-arch-muted">
          {trace.imageCaption}
        </figcaption>
      )}
    </figure>
  )
}

function hasPendingCuratorCheck(building: Building): boolean {
  return [...building.memoryTraces, ...building.artifacts, ...building.timeline].some(
    (item) => item.confidence === 'needs_verification',
  )
}

function BuildingStatusChips({
  building,
  modernPhotoYear,
}: {
  building: Building
  modernPhotoYear?: string
}) {
  const hasVerification =
    Boolean(building.verification?.historicalPhoto) ||
    Boolean(building.verification?.officialExpertise?.length) ||
    Boolean(building.verification?.mediaReports?.length) ||
    building.sources.length > 0
  const hasFieldObservation =
    Boolean(modernPhotoYear) ||
    Boolean(building.verification?.modernPhotoYear) ||
    building.photos.some((photo) => photo.status?.includes('2026'))
  const needsCheck = hasPendingCuratorCheck(building)

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {hasVerification && (
        <span className="arch-pill border-emerald-300 bg-emerald-50 text-emerald-900">
          Проверено источниками
        </span>
      )}
      {hasFieldObservation && (
        <span className="arch-pill border-arch-green/30 bg-arch-green-soft text-arch-green-deep">
          Полевое исследование
        </span>
      )}
      {needsCheck && (
        <span className="arch-pill border-amber-300 bg-amber-50 text-amber-900">
          На проверке у куратора
        </span>
      )}
      {building.cardStatus === 'pilot_in_progress' && (
        <span className="arch-pill border-arch-green/30 bg-arch-green-soft text-arch-green">
          Пилот v{building.cardVersion ?? '0.1'}
        </span>
      )}
    </div>
  )
}

function MaterialsAndSources({ building }: { building: Building }) {
  return (
    <Section title="Материалы и источники">
      <div className="grid gap-5 md:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold text-arch-green-deep">Визуальные материалы</h3>
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
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold text-arch-green-deep">Источники</h3>
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
        </div>
      </div>
    </Section>
  )
}

function SideBySidePhotoComparison({ assets }: { assets: ArchiviewBuildingAssets }) {
  const historicalLabel = assets.historicalPhotoYear
    ? `Фотоматериал ${assets.historicalPhotoYear}`
    : 'Исторический фотоматериал'
  const modernLabel = assets.modernPhotoYear
    ? `Современная съёмка ${assets.modernPhotoYear}`
    : 'Современная съёмка'

  return (
    <div className="space-y-3">
      <p className="rounded-lg border border-arch-line bg-arch-surface-2/50 p-3 text-sm leading-relaxed text-arch-ink/80">
        Это сравнение разных ракурсов. Фотографии не приводятся к одной выпрямленной плоскости и
        не накладываются друг на друга: для идентификации вывесок достаточно видеть, читается ли
        надпись на каждом фотоматериале.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        <figure className="overflow-hidden rounded-xl border border-arch-line bg-arch-surface">
          <div className="border-b border-arch-line px-3 py-2 text-sm font-semibold text-arch-green-deep">
            {historicalLabel}
          </div>
          <img
            src={assets.historicalRectifiedUrl}
            alt={historicalLabel}
            loading="lazy"
            className="max-h-[520px] w-full object-contain"
          />
          <figcaption className="px-3 py-2 text-xs leading-relaxed text-arch-muted">
            На фото фиксируется состояние фасада; для Кривоколенного вывеска «Сжатый газ» здесь не
            читается.
          </figcaption>
        </figure>
        <figure className="overflow-hidden rounded-xl border border-arch-line bg-arch-surface">
          <div className="border-b border-arch-line px-3 py-2 text-sm font-semibold text-arch-green-deep">
            {modernLabel}
          </div>
          <img
            src={assets.modernRectifiedUrl}
            alt={modernLabel}
            loading="lazy"
            className="max-h-[520px] w-full object-contain"
          />
          <figcaption className="px-3 py-2 text-xs leading-relaxed text-arch-muted">
            На современной съёмке виден слой вывески после обнаружения и восстановления.
          </figcaption>
        </figure>
      </div>
    </div>
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

  const isSideBySide = archiview?.labelingLayout === 'side_by_side'

  return (
    <div className="space-y-6">
      <header className="arch-section border-arch-green/20 bg-gradient-to-br from-arch-green-soft to-arch-surface">
        <Link
          to="/"
          className="text-sm font-medium text-arch-green-light hover:text-arch-green-deep"
        >
          ← Карта пилота
        </Link>
        <div className="mt-3">
          <h1 className="text-2xl font-semibold tracking-tight text-arch-green-deep">{building.name}</h1>
        </div>
        <p className="mt-1 text-arch-muted">{building.address}</p>
        <p className="mt-3 text-sm leading-relaxed text-arch-ink/90">{building.headline}</p>
        <BuildingStatusChips building={building} modernPhotoYear={archiview?.modernPhotoYear} />
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

      <Section title="Главный тезис" kicker="Карточка здания">
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

      <Section title="Что видно на фасаде">
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
              <MemoryTraceImage trace={t} />
            </li>
          ))}
        </ul>
        {hasPendingCuratorCheck(building) && (
          <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
            Версии со статусом «Требует проверки» нужно сверить с архивными фотографиями,
            источниками и/или натурным осмотром куратора.
          </p>
        )}
      </Section>

      {archiview ? (
        <>
          <Section title="Сравнение фотоматериалов" kicker="Archiview">
            {(archiview.historicalPhotoYear || archiview.modernPhotoYear) && (
              <p className="mb-3 text-sm leading-relaxed text-arch-muted">
                Фотоматериалы: {archiview.historicalPhotoYear ?? 'архив'} →{' '}
                {archiview.modernPhotoYear ?? 'сегодня'}. Годы обозначают датировку снимков или
                материалов; выводы о событиях опираются на подписи, экспертизы и источники карточки.
              </p>
            )}
            {isSideBySide ? (
              <SideBySidePhotoComparison assets={archiview} />
            ) : (
              <FacadeBeforeAfterSlider
                historicalUrl={archiview.historicalRectifiedUrl}
                modernUrl={archiview.modernRectifiedUrl}
                historicalYear={archiview.historicalPhotoYear}
                modernYear={archiview.modernPhotoYear}
              />
            )}
          </Section>
          {!isSideBySide && (
            <p>
              <Link
                to={`/building/${building.id}/ar`}
                className="inline-flex items-center gap-1 rounded-full border border-arch-line bg-arch-surface px-4 py-2 text-sm font-medium text-arch-green-deep hover:border-arch-green/40 hover:bg-arch-green-soft"
              >
                AR-preview: слои времени на фасаде →
              </Link>
            </p>
          )}
        </>
      ) : null}

      <Section title="Исторические слои">
        <TransformationTimeline stages={building.timeline} />
      </Section>

      {building.artifacts.length > 0 && (
        <Section title="Сохранившиеся элементы">
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

      <MaterialsAndSources building={building} />
    </div>
  )
}
