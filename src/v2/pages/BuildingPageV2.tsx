import { Link, useParams } from 'react-router-dom'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { getBuildingById } from '../../data/buildings'
import { ConfidenceBadge } from '../../components/ConfidenceBadge'
import { ArchiviewFacadePanel } from '../../components/ArchiviewFacadePanel'
import { FacadeTimeLayers } from '../../components/FacadeTimeLayers'
import { FacadeHotspotViewer } from '../../components/FacadeHotspotViewer'
import { TransformationTimeline } from '../../components/TransformationTimeline'
import { getArchiviewAssets } from '../../data/explorer/archiviewAssets'
import {
  fetchExplorerManifest,
  manifestEntryToAssets,
  resolveDefaultComparisonId,
  type ExplorerManifest,
} from '../../data/explorer/explorerManifest'
import { ArchiviewComparisonPicker } from '../../components/ArchiviewComparisonPicker'
import { splitTraceMessage } from '../../lib/traceMessage'
import { getNextTourNavLink } from '../../lib/tourNavigation'
import type { Building, BuildingVerification, MemoryTrace } from '../../types/building'
import type { ArchiviewBuildingAssets } from '../../data/explorer/archiviewAssets'
import { V2Section } from '../components/V2Section'

function timeLayersIntro(cardId?: string): string {
  if (cardId === 'MOSCOW_003') {
    return 'Пока два слоя — фото ~1911 г. (PastVu, до надстройки 1945 г.) и съёмка 2026 (Archiview). JPG в time-layers/ — временные заглушки на общем холсте 4200×2452; позже добавим промежуточные срезы.'
  }
  if (cardId === 'MOSCOW_001') {
    return 'Надстройку по акту экспертизы завершили в 1938 г.; на шкале 1930–1936 — строительство в лесах (Архив ЦИГИ, PastVu p/68053).'
  }
  return ''
}

function publicAssetUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path
  return `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`
}

function v2TourLink(buildingId: string) {
  const next = getNextTourNavLink(buildingId)
  if (next.to.startsWith('/building/')) {
    return { ...next, to: `/v2${next.to}` }
  }
  if (next.to === '/') {
    return { ...next, to: '/v2/map', label: 'На карту →' }
  }
  return next
}

function hasPendingExpertCheck(building: Building): boolean {
  return [...building.memoryTraces, ...building.artifacts, ...building.timeline].some(
    (item) => item.confidence === 'needs_verification',
  )
}

function V2Pill({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'green' | 'amber' }) {
  const tones = {
    neutral: 'border-v2-line bg-v2-surface-muted text-v2-muted',
    green: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    amber: 'border-amber-200 bg-amber-50 text-amber-900',
  }
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-semibold tracking-wide uppercase ${tones[tone]}`}>
      {children}
    </span>
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
    Boolean(building.verification?.confidenceNote?.trim()) ||
    building.sources.length > 0
  const hasFieldObservation =
    Boolean(modernPhotoYear) ||
    Boolean(building.verification?.modernPhotoYear) ||
    building.photos.some((photo) => photo.status?.includes('2026'))
  const needsCheck = hasPendingExpertCheck(building)

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {hasVerification && <V2Pill tone="green">Проверено источниками</V2Pill>}
      {hasFieldObservation && <V2Pill tone="green">Полевое исследование</V2Pill>}
      {needsCheck && <V2Pill tone="amber">На проверке у эксперта</V2Pill>}
      {building.cardStatus === 'pilot_in_progress' && (
        <V2Pill>Пилот v{building.cardVersion ?? '0.1'}</V2Pill>
      )}
    </div>
  )
}

function VerificationBannerV2({ verification }: { verification: BuildingVerification }) {
  const {
    historicalPhoto,
    historicalPhotoYear,
    archivePhotoSources,
    modernPhotoYear,
    officialExpertise,
    confidenceNote,
    overallConfidence,
  } = verification

  const hasExpertise = (officialExpertise?.length ?? 0) > 0
  const hasNote = Boolean(confidenceNote?.trim())
  const archiveSources = archivePhotoSources?.filter(Boolean) ?? []

  if (!historicalPhoto && !hasExpertise && !hasNote && archiveSources.length === 0) return null

  return (
    <div className="v2-card border-v2-red/20 bg-v2-surface p-5">
      <p className="v2-kicker">Достоверность</p>
      <ul className="mt-3 space-y-3 text-sm text-v2-muted">
        {historicalPhoto && archiveSources.length > 0 ? (
          <li>
            <V2Pill tone="green">Архивные фотоматериалы</V2Pill>
            <p className="mt-2 leading-relaxed">
              {[
                ...archiveSources,
                ...(modernPhotoYear ? [`Съёмка ${modernPhotoYear} (Archiview)`] : []),
              ].join(', ')}
            </p>
          </li>
        ) : historicalPhoto ? (
          <li className="flex flex-wrap items-center gap-2">
            <V2Pill tone="green">Есть исторический фотоматериал</V2Pill>
            {historicalPhotoYear && (
              <span>
                архив {historicalPhotoYear}
                {modernPhotoYear ? ` · съёмка ${modernPhotoYear}` : ''}
              </span>
            )}
          </li>
        ) : null}
        {officialExpertise?.map((item) => (
          <li key={item.url} className="flex flex-wrap items-center gap-2">
            <V2Pill>С официальной экспертизой</V2Pill>
            <a href={item.url} target="_blank" rel="noreferrer" className="text-v2-blue underline">
              {item.title}
            </a>
          </li>
        ))}
        {hasNote && <li className="leading-relaxed">{confidenceNote}</li>}
        {overallConfidence && (
          <li className="flex items-center gap-2">
            <span className="text-v2-ink">Общая оценка:</span>
            <ConfidenceBadge level={overallConfidence} />
          </li>
        )}
      </ul>
    </div>
  )
}

function MemoryTraceImage({ trace }: { trace: MemoryTrace }) {
  const [hidden, setHidden] = useState(false)
  if (!trace.imagePath || hidden) return null

  return (
    <figure className="mt-3 overflow-hidden rounded-lg border border-v2-line bg-v2-surface-muted">
      <img
        src={publicAssetUrl(trace.imagePath)}
        alt={trace.imageCaption ?? trace.title}
        loading="lazy"
        onError={() => setHidden(true)}
        className="max-h-72 w-full object-cover"
      />
      {trace.imageCaption && (
        <figcaption className="px-3 py-2 text-xs leading-relaxed text-v2-muted">
          {trace.imageCaption}
        </figcaption>
      )}
    </figure>
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
    <div className="space-y-4">
      <p className="rounded-lg border border-v2-line bg-v2-surface-muted p-3 text-sm leading-relaxed text-v2-muted">
        Сравнение разных ракурсов без приведения к одной плоскости — для идентификации вывесок и
        надписей на каждом снимке.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        {[historicalLabel, modernLabel].map((label, i) => (
          <figure key={label} className="overflow-hidden rounded-lg border border-v2-line bg-v2-surface">
            <div className="border-b border-v2-line px-3 py-2 text-xs font-bold tracking-wide text-v2-ink uppercase">
              {label}
            </div>
            <img
              src={i === 0 ? assets.historicalRectifiedUrl : assets.modernRectifiedUrl}
              alt={label}
              loading="lazy"
              className="max-h-[520px] w-full object-contain"
            />
          </figure>
        ))}
      </div>
    </div>
  )
}

function MaterialsAndSources({ building }: { building: Building }) {
  return (
    <V2Section title="Материалы и источники">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-v2-ink uppercase">
            Визуальные материалы
          </h3>
          <ul className="space-y-2 text-sm text-v2-muted">
            {building.photos.map((p) => (
              <li key={p.id}>
                {p.url ? (
                  <a href={p.url} target="_blank" rel="noreferrer" className="text-v2-blue underline">
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
        </div>
        <div>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-v2-ink uppercase">Источники</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-v2-muted">
            {building.sources.map((s) => (
              <li key={s.id}>
                {s.url ? (
                  <a href={s.url} target="_blank" rel="noreferrer" className="text-v2-blue underline">
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
    </V2Section>
  )
}

export function BuildingPageV2() {
  const { id } = useParams<{ id: string }>()
  const building = id ? getBuildingById(id) : undefined
  const archiview = building ? getArchiviewAssets(building.id) : undefined
  const [manifest, setManifest] = useState<ExplorerManifest | null>(null)
  const [selectedComparisonId, setSelectedComparisonId] = useState('')

  useEffect(() => {
    if (!archiview?.cardId) {
      setManifest(null)
      setSelectedComparisonId('')
      return
    }
    let cancelled = false
    fetchExplorerManifest(archiview.cardId).then((data) => {
      if (cancelled) return
      setManifest(data)
      if (data?.comparisons?.length) {
        setSelectedComparisonId(resolveDefaultComparisonId(data))
      }
    })
    return () => {
      cancelled = true
    }
  }, [archiview?.cardId])

  const displayAssets = useMemo(() => {
    if (!archiview) return undefined
    if (!manifest || manifest.comparisons.length <= 1) return archiview
    const entry =
      manifest.comparisons.find((c) => c.comparisonId === selectedComparisonId) ??
      manifest.comparisons.find((c) => c.comparisonId === resolveDefaultComparisonId(manifest)) ??
      manifest.comparisons[0]
    return manifestEntryToAssets(archiview.cardId, archiview.buildingId, entry, archiview)
  }, [archiview, manifest, selectedComparisonId])

  if (!building) {
    return (
      <div className="v2-container py-10">
        <p className="text-v2-muted">
          Здание не найдено.{' '}
          <Link to="/v2/map" className="font-medium text-v2-blue underline">
            На карту
          </Link>
        </p>
      </div>
    )
  }

  const isSideBySide = displayAssets?.labelingLayout === 'side_by_side'
  const timeLayersIntroText = timeLayersIntro(building.cardId)
  const nextTourStop = v2TourLink(building.id)

  return (
    <div className="v2-building pb-16">
      <div className="v2-container space-y-6 py-8 sm:py-10">
        <header className="v2-card p-6 sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link to="/v2/map" className="text-sm font-medium text-v2-muted transition hover:text-v2-ink">
              ← Карта
            </Link>
            <Link
              to={nextTourStop.to}
              aria-label={nextTourStop.ariaLabel}
              className="text-sm font-medium text-v2-muted transition hover:text-v2-ink"
            >
              {nextTourStop.label}
            </Link>
          </div>

          {building.cardId ? <p className="v2-kicker mt-6">{building.cardId}</p> : null}
          <h1 className="mt-2 text-2xl leading-tight font-semibold tracking-tight sm:text-3xl">
            {building.name}
          </h1>
          <p className="mt-2 text-sm text-v2-muted">{building.address}</p>
          <p className="mt-4 text-base leading-relaxed text-v2-ink">{building.headline}</p>

          <BuildingStatusChips building={building} modernPhotoYear={archiview?.modernPhotoYear} />

          <div className="mt-4 flex flex-wrap gap-2 text-sm text-v2-muted">
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

          <p className="mt-5 border-t border-v2-line pt-5 text-sm leading-relaxed text-v2-muted">
            {building.summary}
          </p>
        </header>

        {building.verification && <VerificationBannerV2 verification={building.verification} />}

        {displayAssets ? (
          <section className="v2-card overflow-hidden">
            <div className="space-y-4 px-5 pt-5 sm:px-6">
              <div>
                <p className="v2-kicker">Archiview</p>
                <h2 className="v2-section-title mt-1">Фасад и подсветка</h2>
              </div>
              {manifest && manifest.comparisons.length > 1 ? (
                <ArchiviewComparisonPicker
                  manifest={manifest}
                  selectedId={selectedComparisonId}
                  onSelect={setSelectedComparisonId}
                />
              ) : null}
            </div>
            <ArchiviewFacadePanel assets={displayAssets} building={building} />
          </section>
        ) : (
          <V2Section title="Фасад и подсветка">
            <FacadeHotspotViewer building={building} />
          </V2Section>
        )}

        <V2Section title="Что видно на фасаде">
          <ul className="space-y-3">
            {building.memoryTraces.map((t) => {
              const { body, source } = splitTraceMessage(t.userMessage)
              return (
                <li
                  key={t.id}
                  className="rounded-lg border border-v2-line bg-v2-surface-muted/60 p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-medium text-v2-ink">{t.title}</h3>
                    <ConfidenceBadge level={t.confidence} />
                    <span className="text-xs text-v2-muted">{t.period}</span>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-v2-muted">{body}</p>
                  {source ? (
                    <p className="mt-2 text-xs text-v2-muted">Источник: {source}</p>
                  ) : null}
                  <MemoryTraceImage trace={t} />
                </li>
              )
            })}
          </ul>
          {hasPendingExpertCheck(building) && (
            <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">
              Версии со статусом «Требует проверки» нужно сверить с архивными фотографиями,
              источниками и/или натурным осмотром эксперта.
            </p>
          )}
        </V2Section>

        {displayAssets && !isSideBySide ? (
          <V2Section title="Слои времени" kicker="Archiview">
            <p className="mb-4 text-sm leading-relaxed text-v2-muted">
              Двигайте ползунок по годам — снимки сменяют друг друга через плавное затемнение.
              {timeLayersIntroText ? ` ${timeLayersIntroText}` : null}
            </p>
            <FacadeTimeLayers building={building} archiview={archiview ?? displayAssets} />
          </V2Section>
        ) : null}

        {displayAssets && isSideBySide ? (
          <V2Section title="Сравнение фотоматериалов" kicker="Archiview">
            {(displayAssets.historicalPhotoYear || displayAssets.modernPhotoYear) && (
              <p className="mb-3 text-sm text-v2-muted">
                Фотоматериалы: {displayAssets.historicalPhotoYear ?? 'архив'} →{' '}
                {displayAssets.modernPhotoYear ?? 'сегодня'}.
              </p>
            )}
            <SideBySidePhotoComparison assets={displayAssets} />
          </V2Section>
        ) : null}

        <V2Section title="Исторические слои">
          <TransformationTimeline stages={building.timeline} />
        </V2Section>

        {building.artifacts.length > 0 && (
          <V2Section title="Сохранившиеся элементы">
            <ul className="space-y-2">
              {building.artifacts.map((a) => (
                <li key={a.id} className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-medium text-v2-ink">{a.title}</span>
                  <ConfidenceBadge level={a.confidence} />
                  <span className="text-v2-muted">{a.period}</span>
                </li>
              ))}
            </ul>
          </V2Section>
        )}

        <MaterialsAndSources building={building} />
      </div>
    </div>
  )
}
