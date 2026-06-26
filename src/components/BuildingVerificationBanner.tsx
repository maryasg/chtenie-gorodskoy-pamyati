import type { BuildingVerification } from '../types/building'
import { ConfidenceBadge } from './ConfidenceBadge'

export function BuildingVerificationBanner({ verification }: { verification: BuildingVerification }) {
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
    <div className="rounded-xl border border-arch-green/25 bg-gradient-to-br from-arch-green-soft to-arch-surface p-4 shadow-sm">
      <p className="arch-kicker text-arch-green">Достоверность</p>
      <ul className="mt-2 space-y-2">
        {historicalPhoto && archiveSources.length > 0 ? (
          <li className="text-sm text-arch-ink">
            <span className="inline-flex rounded-full border border-arch-green/35 bg-arch-green-soft px-2.5 py-0.5 text-xs font-medium text-arch-green-deep">
              Архивные материалы
            </span>
            <ul className="mt-2 list-inside list-disc space-y-0.5 text-arch-muted">
              {archiveSources.map((item) => (
                <li key={item}>{item}</li>
              ))}
              {modernPhotoYear ? <li>Съёмка {modernPhotoYear} (Archiview)</li> : null}
            </ul>
          </li>
        ) : historicalPhoto ? (
          <li className="flex flex-wrap items-center gap-2 text-sm text-arch-ink">
            <span className="inline-flex rounded-full border border-arch-green/35 bg-arch-green-soft px-2.5 py-0.5 text-xs font-medium text-arch-green-deep">
              Есть исторический фотоматериал
            </span>
            {historicalPhotoYear && (
              <span className="text-arch-muted">
                архив {historicalPhotoYear}
                {modernPhotoYear ? ` · съёмка ${modernPhotoYear}` : ''}
              </span>
            )}
          </li>
        ) : null}
        {officialExpertise?.map((item) => (
          <li key={item.url} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="inline-flex rounded-full border border-blue-300 bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-900">
              Официальная экспертиза
            </span>
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="text-blue-800 underline decoration-blue-300 underline-offset-2 hover:text-blue-950"
            >
              {item.title}
              {item.issuedAt ? ` (${item.issuedAt})` : ''}
            </a>
          </li>
        ))}
      </ul>
      {hasNote && (
        <div className="mt-3 rounded-lg border border-arch-line/80 bg-arch-surface/80 px-3 py-2.5">
          {overallConfidence ? (
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-arch-muted">Принцип оценки</span>
              <ConfidenceBadge level={overallConfidence} />
            </div>
          ) : null}
          <p className="text-sm leading-relaxed text-arch-ink/85">{confidenceNote}</p>
        </div>
      )}
    </div>
  )
}
