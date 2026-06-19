import type { ExplorerManifest } from '../data/explorer/explorerManifest'

export function ArchiviewComparisonPicker({
  manifest,
  selectedId,
  onSelect,
}: {
  manifest: ExplorerManifest
  selectedId: string
  onSelect: (comparisonId: string) => void
}) {
  if (manifest.comparisons.length <= 1) return null

  return (
    <div className="mb-4 space-y-2">
      <p className="text-sm leading-relaxed text-arch-muted">
        На этом доме несколько сравнений Archiview — разные пары «история → современность». Выберите по годам:
      </p>
      <div className="flex flex-wrap gap-2">
        {manifest.comparisons.map((c) => {
          const active = c.comparisonId === selectedId
          const isDefault = c.comparisonId === manifest.defaultComparisonId
          const yearLabel =
            c.historicalPhotoYear && c.modernPhotoYear
              ? `${c.historicalPhotoYear} → ${c.modernPhotoYear}`
              : c.historicalPhotoYear || c.title || c.comparisonId
          return (
            <button
              key={c.comparisonId}
              type="button"
              onClick={() => onSelect(c.comparisonId)}
              className={`rounded-full border px-3 py-1.5 text-sm transition ${
                active
                  ? 'border-arch-green bg-arch-green-soft font-semibold text-arch-green-deep'
                  : 'border-arch-line bg-arch-surface text-arch-ink hover:border-arch-green/40'
              }`}
            >
              {isDefault ? '★ ' : ''}
              {yearLabel}
              {c.title && c.historicalPhotoYear ? ` (${c.title})` : ''}
              {c.annotationCount != null && c.annotationCount > 0 ? ` · ${c.annotationCount} обл.` : ''}
              {c.isLegacy ? ' (legacy)' : ''}
            </button>
          )
        })}
      </div>
    </div>
  )
}
