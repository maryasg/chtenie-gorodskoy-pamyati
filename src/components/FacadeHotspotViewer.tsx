import { useState } from 'react'
import type { Building, Hotspot } from '../types/building'
import { ConfidenceBadge } from './ConfidenceBadge'

export function FacadeHotspotViewer({ building }: { building: Building }) {
  const [active, setActive] = useState<Hotspot | null>(null)

  const facadePhoto = building.photos.find((p) => p.type === 'facade')
  const hasHotspots = building.hotspots.length > 0

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

  return (
    <div className="space-y-3">
      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl border border-stone-200 bg-gradient-to-b from-stone-200 to-stone-300">
        {facadePhoto?.status === 'предстоит съёмка' && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-stone-900/40 p-4 text-center text-sm text-white">
            Современное фото фасада предстоит съёмке. Hotspots — ориентировочные для демо.
          </div>
        )}
        <div className="absolute inset-0 flex items-end justify-center pb-8 text-center text-xs text-stone-600">
          {building.name} — схема фасада
        </div>
        {hasHotspots &&
          building.hotspots.map((hs) => (
            <button
              key={hs.id}
              type="button"
              title={hs.label}
              onClick={() => setActive(hs)}
              className={`absolute rounded border-2 transition ${
                active?.id === hs.id
                  ? 'border-amber-400 bg-amber-400/40'
                  : 'border-red-500/80 bg-red-500/25 hover:bg-red-500/40'
              }`}
              style={{
                left: `${hs.x}%`,
                top: `${hs.y}%`,
                width: `${hs.width ?? 8}%`,
                height: `${hs.height ?? 8}%`,
              }}
            />
          ))}
      </div>

      {active && (
        <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
          {(() => {
            const d = resolveDetail(active)
            return (
              <>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <h4 className="font-semibold">{d.title}</h4>
                  <ConfidenceBadge level={d.confidence} />
                </div>
                <p className="text-sm text-stone-700">{d.body}</p>
                <p className="mt-2 text-xs text-stone-500">
                  Видимый след на фасаде · в AR-версии — подсветка через камеру
                </p>
              </>
            )
          })()}
        </div>
      )}

      {!hasHotspots && (
        <p className="text-sm text-stone-500">
          Точки на фасаде появятся после съёмки и разметки. См. архивные фото ниже.
        </p>
      )}
    </div>
  )
}
