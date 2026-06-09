import { useCallback, useEffect, useRef, useState } from 'react'

type Props = {
  historicalUrl: string
  modernUrl: string
  historicalYear?: string
  modernYear?: string
}

type AssetCheck = {
  historicalUrl: string
  modernUrl: string
  status: 'loading' | 'ready' | 'error'
}

export function FacadeBeforeAfterSlider({
  historicalUrl,
  modernUrl,
  historicalYear,
  modernYear,
}: Props) {
  const [split, setSplit] = useState(50)
  const [assetCheck, setAssetCheck] = useState<AssetCheck>({
    historicalUrl,
    modernUrl,
    status: 'loading',
  })
  const dragging = useRef(false)
  const stageRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false

    const check = async () => {
      try {
        const [hRes, mRes] = await Promise.all([
          fetch(historicalUrl, { method: 'HEAD' }),
          fetch(modernUrl, { method: 'HEAD' }),
        ])
        if (cancelled) return
        setAssetCheck({
          historicalUrl,
          modernUrl,
          status: hRes.ok && mRes.ok ? 'ready' : 'error',
        })
      } catch {
        if (cancelled) return
        setAssetCheck({ historicalUrl, modernUrl, status: 'error' })
      }
    }
    check()
    return () => {
      cancelled = true
    }
  }, [historicalUrl, modernUrl])

  const setSplitFromClientX = useCallback((clientX: number) => {
    const el = stageRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (rect.width <= 0) return
    const pct = ((clientX - rect.left) / rect.width) * 100
    setSplit(Math.max(0, Math.min(100, pct)))
  }, [])

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (!dragging.current) return
      setSplitFromClientX(e.clientX)
    }
    const onUp = () => {
      dragging.current = false
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [setSplitFromClientX])

  const assetStatus =
    assetCheck.historicalUrl === historicalUrl && assetCheck.modernUrl === modernUrl
      ? assetCheck.status
      : 'loading'

  if (assetStatus === 'error') {
    return (
      <p className="rounded-lg border border-dashed border-arch-line bg-arch-surface-2/60 p-4 text-sm text-arch-muted">
        Пара для сравнения ещё не на сайте. В Archiview: вкладка 2 → подготовить выпрямление, затем{' '}
        <code>copy_to_website.bat</code> → Push.
      </p>
    )
  }

  if (assetStatus !== 'ready') {
    return <p className="text-sm text-arch-muted">Загрузка сравнения…</p>
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-arch-muted">
        Две выпрямленные реальности из Archiview: слева — исторический фасад, справа — современный.
        Тяните ползунок или линию на фото.
      </p>

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-arch-line bg-arch-surface px-3 py-2">
        <label className="flex min-w-[200px] flex-1 items-center gap-2 text-sm text-arch-ink">
          <span className="shrink-0 whitespace-nowrap">Граница</span>
          <input
            type="range"
            min={0}
            max={100}
            value={split}
            onChange={(e) => setSplit(Number(e.target.value))}
            className="w-full accent-arch-green"
            aria-valuetext={`${Math.round(split)}%`}
          />
          <span className="w-10 shrink-0 text-right font-medium tabular-nums">{Math.round(split)}%</span>
        </label>
        <span className="text-xs text-arch-muted">← история · современность →</span>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-stretch">
        <div
          ref={stageRef}
          className="relative min-w-0 flex-1 select-none overflow-hidden rounded-xl border border-arch-line bg-arch-green-deep shadow-md"
          onPointerDown={(e) => {
            if (e.button !== 0) return
            dragging.current = true
            setSplitFromClientX(e.clientX)
          }}
        >
          <img
            src={historicalUrl}
            alt={`Исторический фасад${historicalYear ? `, ${historicalYear}` : ''}`}
            className="block max-h-[min(78vh,820px)] w-full object-contain"
            draggable={false}
          />
          <img
            src={modernUrl}
            alt={`Современный фасад${modernYear ? `, ${modernYear}` : ''}`}
            className="pointer-events-none absolute inset-0 block max-h-[min(78vh,820px)] w-full object-contain"
            style={{ clipPath: `inset(0 0 0 ${split}%)` }}
            draggable={false}
          />
          <div
            className="pointer-events-none absolute inset-y-0 z-10 w-0.5 bg-arch-gold shadow-[0_0_8px_rgba(184,134,11,0.7)]"
            style={{ left: `${split}%`, transform: 'translateX(-50%)' }}
            aria-hidden
          />
          <div
            className="pointer-events-none absolute top-1/2 z-10 flex h-10 w-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-arch-gold bg-arch-surface/95 text-arch-green-deep shadow-md"
            style={{ left: `${split}%` }}
            aria-hidden
          >
            ↔
          </div>
        </div>

        {(historicalYear || modernYear) && (
          <div className="flex shrink-0 flex-row justify-center gap-6 sm:w-28 sm:flex-col sm:justify-center sm:gap-8 sm:py-4">
            {historicalYear && (
              <div className="text-center sm:text-left">
                <p className="text-3xl font-semibold tabular-nums leading-none text-arch-green-deep">
                  {historicalYear}
                </p>
                <p className="mt-1 text-xs uppercase tracking-wide text-arch-muted">история</p>
              </div>
            )}
            {modernYear && (
              <div className="text-center sm:text-left">
                <p className="text-3xl font-semibold tabular-nums leading-none text-arch-green-deep">
                  {modernYear}
                </p>
                <p className="mt-1 text-xs uppercase tracking-wide text-arch-muted">сегодня</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
