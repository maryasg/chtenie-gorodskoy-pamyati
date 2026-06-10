import { useState } from 'react'
import type { Building, Hotspot } from '../types/building'
import { ConfidenceBadge } from './ConfidenceBadge'

export function FacadeHotspotViewer({ building }: { building: Building }) {
  const [active, setActive] = useState<Hotspot | null>(null)
  const [hovered, setHovered] = useState<Hotspot | null>(null)

  const facadePhoto = building.photos.find((p) => p.type === 'facade')
  const hasHotspots = building.hotspots.length > 0
  const display = hovered ?? active

  const resolveDetail = (hs: Hotspot) => {
    if (hs.traceId) {
      const trace = building.memoryTraces.find((t) => t.id === hs.traceId)
      if (trace) {
        return {
          title: trace.title,
          body: trace.userMessage,
          confidence: trace.confidence,
        }
      }
    }
    if (hs.artifactId) {
      const art = building.artifacts.find((a) => a.id === hs.artifactId)
      if (art) {
        return {
          title: art.title,
          body: art.location ?? 'Сохранившийся артефакт фасада',
          confidence: art.confidence,
        }
      }
    }
    return { title: hs.label, body: '', confidence: 'confirmed' as const }
  }

  const labelFor = (hs: Hotspot) => resolveDetail(hs).title

  return (
    <div className="space-y-3">
      <div
        className="relative aspect-[4/3] w-full overflow-hidden rounded-xl border border-arch-line bg-gradient-to-b from-arch-surface-2 to-arch-green-soft"
        onMouseLeave={() => setHovered(null)}
      >
        {facadePhoto?.status === 'предстоит съёмка' && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-arch-green-deep/55 p-4 text-center text-sm text-arch-surface">
            Современное фото фасада предстоит съёмке. Hotspots — ориентировочные для демо.
          </div>
        )}
        <div className="absolute inset-0 flex items-end justify-center pb-8 text-center text-xs text-arch-muted">
          {building.name} — схема фасада
        </div>
        {hasHotspots &&
          building.hotspots.map((hs) => {
            const isOn = display?.id === hs.id
            return (
              <div key={hs.id}>
                <button
                  type="button"
                  aria-label={labelFor(hs)}
                  onMouseEnter={() => setHovered(hs)}
                  onFocus={() => setHovered(hs)}
                  onClick={() => setActive(hs)}
                  className={`absolute rounded border-2 transition ${
                    isOn
                      ? 'border-arch-gold bg-arch-gold/45 z-20'
                      : 'border-arch-accent/80 bg-arch-accent/25 hover:bg-arch-accent/40 z-10'
                  }`}
                  style={{
                    left: `${hs.x}%`,
                    top: `${hs.y}%`,
                    width: `${hs.width ?? 8}%`,
                    height: `${hs.height ?? 8}%`,
                  }}
                />
                {isOn && (
                  <div
                    className="pointer-events-none absolute z-30 max-w-[min(90%,220px)] rounded-md border border-arch-gold bg-arch-surface px-2 py-1 text-xs font-semibold text-arch-ink shadow-md"
                    style={{
                      left: `${Math.min(hs.x + (hs.width ?? 8) / 2, 72)}%`,
                      top: `${Math.max(hs.y - 4, 2)}%`,
                      transform: 'translate(-50%, -100%)',
                    }}
                  >
                    {labelFor(hs)}
                  </div>
                )}
              </div>
            )
          })}
      </div>

      {display && (
        <div className="rounded-xl border border-arch-line bg-arch-surface p-4 shadow-sm">
          {(() => {
            const d = resolveDetail(display)
            return (
              <>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <h4 className="font-semibold text-arch-green-deep">{d.title}</h4>
                  <ConfidenceBadge level={d.confidence} />
                </div>
                <p className="text-sm text-arch-ink/80">{d.body}</p>
                <p className="mt-2 text-xs text-arch-muted">
                  Наведите на другую область — подпись обновится
                </p>
              </>
            )
          })()}
        </div>
      )}

      {!hasHotspots && (
        <p className="text-sm text-arch-muted">
          Точки на фасаде появятся после съёмки и разметки. См. архивные фото ниже.
        </p>
      )}
    </div>
  )
}
