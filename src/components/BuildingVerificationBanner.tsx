import type { BuildingVerification } from '../types/building'

export function BuildingVerificationBanner({ verification }: { verification: BuildingVerification }) {
  const { historicalPhoto, historicalPhotoYear, modernPhotoYear, officialExpertise, mediaReports } =
    verification
  const hasExpertise = (officialExpertise?.length ?? 0) > 0
  const hasMedia = (mediaReports?.length ?? 0) > 0

  if (!historicalPhoto && !hasExpertise && !hasMedia) return null

  return (
    <div className="rounded-xl border border-arch-green/25 bg-gradient-to-br from-arch-green-soft to-arch-surface p-4 shadow-sm">
      <p className="arch-kicker text-arch-green">Достоверность</p>
      <ul className="mt-2 space-y-2">
        {historicalPhoto && (
          <li className="flex flex-wrap items-center gap-2 text-sm text-arch-ink">
            <span className="inline-flex rounded-full border border-arch-green/35 bg-arch-green-soft px-2.5 py-0.5 text-xs font-medium text-arch-green-deep">
              Подтверждено историческим фото
            </span>
            {historicalPhotoYear && (
              <span className="text-arch-muted">
                архив {historicalPhotoYear}
                {modernPhotoYear ? ` · съёмка ${modernPhotoYear}` : ''}
              </span>
            )}
          </li>
        )}
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
        {mediaReports?.map((item) => (
          <li key={item.url} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="inline-flex rounded-full border border-amber-300 bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-950">
              Публикация СМИ
            </span>
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="text-amber-950 underline decoration-amber-400 underline-offset-2 hover:text-stone-900"
            >
              {item.outlet ? `${item.outlet}: ` : ''}
              {item.title}
              {item.issuedAt ? ` (${item.issuedAt})` : ''}
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
