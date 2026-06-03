import type { BuildingVerification } from '../types/building'

export function BuildingVerificationBanner({ verification }: { verification: BuildingVerification }) {
  const { historicalPhoto, historicalPhotoYear, modernPhotoYear, officialExpertise } = verification
  const hasExpertise = (officialExpertise?.length ?? 0) > 0

  if (!historicalPhoto && !hasExpertise) return null

  return (
    <div className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Достоверность</p>
      <ul className="mt-2 space-y-2">
        {historicalPhoto && (
          <li className="flex flex-wrap items-center gap-2 text-sm text-stone-800">
            <span className="inline-flex rounded-full border border-emerald-300 bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-900">
              Подтверждено историческим фото
            </span>
            {historicalPhotoYear && (
              <span className="text-stone-600">
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
      </ul>
    </div>
  )
}
