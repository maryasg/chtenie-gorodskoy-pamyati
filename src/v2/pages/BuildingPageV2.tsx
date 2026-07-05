import { Link, useParams } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { getBuildingById } from '../../data/buildings'
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
import { V2Plate, V2Manifest } from '../components/V2Plate'
import { V2ConfidenceBadge } from '../components/V2ConfidenceBadge'
import { V2SquareMark } from '../components/V2SquareMark'
import { V2_CONFIDENCE_DOT } from '../lib/confidenceColors'

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

function V2StatusPlate({ code, title, active = true }: { code: string; title: string; active?: boolean }) {
  return (
    <div className="inline-flex items-center gap-2 border border-v2-line bg-v2-surface px-2.5 py-1.5">
      <V2SquareMark active={active} />
      <span className="v2-mono-xs text-v2-ink">{code}</span>
      <span className="text-[11px] text-v2-muted normal-case">{title}</span>
    </div>
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
      {hasVerification && <V2StatusPlate code="SRC" title="Проверено источниками" />}
      {hasFieldObservation && <V2StatusPlate code="FLD" title="Полевое исследование" />}
      {needsCheck && (
        <V2StatusPlate code="REV" title="На проверке" active={false} />
      )}
      {building.cardStatus === 'pilot_in_progress' && (
        <V2StatusPlate
          code={`V${building.cardVersion ?? '0.1'}`}
          title="Пилот"
          active={false}
        />
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
    <V2Manifest kicker="Confidence" title="Достоверность" className="normal-case">
      <ul>
        {historicalPhoto && archiveSources.length > 0 ? (
          <V2Plate
            code="ARC"
            title="Архивные фотоматериалы"
            description={[
              ...archiveSources,
              ...(modernPhotoYear ? [`Съёмка ${modernPhotoYear} (Archiview)`] : []),
            ].join(', ')}
            markColor={V2_CONFIDENCE_DOT.confirmed}
            active
          />
        ) : historicalPhoto ? (
          <V2Plate
            code="ARC"
            title="Исторический фотоматериал"
            description={[
              historicalPhotoYear ? `архив ${historicalPhotoYear}` : null,
              modernPhotoYear ? `съёмка ${modernPhotoYear}` : null,
            ]
              .filter(Boolean)
              .join(' · ')}
            markColor={V2_CONFIDENCE_DOT.confirmed}
            active
          />
        ) : null}
        {officialExpertise?.map((item) => (
          <V2Plate
            key={item.url}
            code="EXP"
            title="Официальная экспертиза"
            description={
              <a href={item.url} target="_blank" rel="noreferrer" className="v2-btn-text normal-case">
                {item.title} →
              </a>
            }
            markColor={V2_CONFIDENCE_DOT.confirmed}
          />
        ))}
        {hasNote ? (
          <V2Plate code="NOTE" title="Примечание" description={confidenceNote!} markColor={V2_CONFIDENCE_DOT.probable} />
        ) : null}
        {overallConfidence ? (
          <V2Plate
            code="LVL"
            title="Общая оценка"
            description={<V2ConfidenceBadge level={overallConfidence} />}
            markColor={V2_CONFIDENCE_DOT[overallConfidence]}
          />
        ) : null}
      </ul>
    </V2Manifest>
  )
}

function MemoryTraceImage({ trace }: { trace: MemoryTrace }) {
  const [hidden, setHidden] = useState(false)
  if (!trace.imagePath || hidden) return null

  return (
    <figure className="mt-3 overflow-hidden border border-v2-line bg-v2-surface-muted">
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
        <header className="v2-panel px-4 py-6 sm:px-6 sm:py-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link to="/v2/map" className="v2-btn-text">
              ← Карта
            </Link>
            <Link
              to={nextTourStop.to}
              aria-label={nextTourStop.ariaLabel}
              className="v2-btn-text"
            >
              {nextTourStop.label}
            </Link>
          </div>

          {building.cardId ? <p className="v2-kicker mt-6">REF · {building.cardId}</p> : null}
          <h1 className="v2-display mt-2 text-3xl leading-tight sm:text-4xl">{building.name}</h1>
          <p className="v2-mono-xs mt-3 text-v2-muted normal-case">{building.address}</p>
          <p className="mt-4 text-sm leading-relaxed text-v2-muted normal-case">{building.headline}</p>

          <BuildingStatusChips building={building} modernPhotoYear={archiview?.modernPhotoYear} />

          <div className="mt-4 flex flex-wrap gap-2 text-sm text-v2-muted normal-case">
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
          <section className="v2-panel overflow-hidden">
            <header className="border-b border-v2-line px-4 py-4 sm:px-5">
              <p className="v2-kicker">Archiview</p>
              <h2 className="v2-section-title mt-1">Фасад и подсветка</h2>
            </header>
            {manifest && manifest.comparisons.length > 1 ? (
              <div className="border-b border-v2-line px-4 py-3 sm:px-5">
                <ArchiviewComparisonPicker
                  manifest={manifest}
                  selectedId={selectedComparisonId}
                  onSelect={setSelectedComparisonId}
                />
              </div>
            ) : null}
            <ArchiviewFacadePanel assets={displayAssets} building={building} />
          </section>
        ) : (
          <V2Section title="Фасад и подсветка">
            <FacadeHotspotViewer building={building} />
          </V2Section>
        )}

        <V2Manifest
          kicker="Layer manifest"
          title="Что видно на фасаде"
          count={`${building.memoryTraces.length} ELEMENTS`}
        >
          {building.memoryTraces.map((t, index) => {
            const { body, source } = splitTraceMessage(t.userMessage)
            const code = `T${String(index + 1).padStart(2, '0')}`
            return (
              <V2Plate
                key={t.id}
                code={code}
                title={t.title}
                description={body}
                meta={t.period}
                markColor={V2_CONFIDENCE_DOT[t.confidence]}
                active={t.confidence === 'confirmed'}
              >
                {source ? (
                  <p className="text-xs text-v2-muted">Источник: {source}</p>
                ) : null}
                <div className="mt-2">
                  <V2ConfidenceBadge level={t.confidence} />
                </div>
                <MemoryTraceImage trace={t} />
              </V2Plate>
            )
          })}
          {hasPendingExpertCheck(building) && (
            <div className="v2-plate-row">
              <div className="flex gap-3">
                <V2SquareMark innerColor={V2_CONFIDENCE_DOT.needs_verification} />
                <p className="text-sm leading-relaxed text-v2-muted normal-case">
                  Версии со статусом «Требует проверки» нужно сверить с архивными фотографиями,
                  источниками и/или натурным осмотром эксперта.
                </p>
              </div>
            </div>
          )}
        </V2Manifest>

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
          <V2Manifest
            kicker="Artifacts"
            title="Сохранившиеся элементы"
            count={`${building.artifacts.length} ITEMS`}
          >
            {building.artifacts.map((a, index) => (
              <V2Plate
                key={a.id}
                code={`A${String(index + 1).padStart(2, '0')}`}
                title={a.title}
                meta={a.period}
                markColor={V2_CONFIDENCE_DOT[a.confidence]}
              >
                <V2ConfidenceBadge level={a.confidence} />
              </V2Plate>
            ))}
          </V2Manifest>
        )}

        <MaterialsAndSources building={building} />
      </div>
    </div>
  )
}
