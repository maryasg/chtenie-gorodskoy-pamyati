import { useCallback, useEffect, useRef, useState } from 'react'

type Props = {
  historicalUrl: string
  modernUrl: string
}

export function FacadeBeforeAfterSlider({ historicalUrl, modernUrl }: Props) {
  const [split, setSplit] = useState(50)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState(false)
  const dragging = useRef(false)
  const stageRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    setReady(false)
    setError(false)

    const check = async () => {
      const [hRes, mRes] = await Promise.all([
        fetch(historicalUrl, { method: 'HEAD' }),
        fetch(modernUrl, { method: 'HEAD' }),
      ])
      if (cancelled) return
      if (hRes.ok && mRes.ok) setReady(true)
      else setError(true)
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

  if (error) {
    return (
      <p className="rounded-lg border border-dashed border-stone-300 bg-stone-50 p-4 text-sm text-stone-600">
        Пара для сравнения ещё не на сайте. В Archiview: вкладка 2 → подготовить выпрямление, затем{' '}
        <code>copy_to_website.bat</code> → Push.
      </p>
    )
  }

  if (!ready) {
    return <p className="text-sm text-stone-500">Загрузка сравнения…</p>
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-stone-600">
        Две выпрямленные реальности из Archiview: слева — исторический фасад, справа — современный.
        Тяните ползунок или линию на фото.
      </p>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-stone-200 bg-white px-3 py-2">
        <label className="flex min-w-[200px] flex-1 items-center gap-2 text-sm text-stone-700">
          <span className="shrink-0 whitespace-nowrap">Граница</span>
          <input
            type="range"
            min={0}
            max={100}
            value={split}
            onChange={(e) => setSplit(Number(e.target.value))}
            className="w-full accent-amber-600"
            aria-valuetext={`${Math.round(split)}%`}
          />
          <span className="w-10 shrink-0 text-right font-medium tabular-nums">{Math.round(split)}%</span>
        </label>
        <span className="text-xs text-stone-500">← история · современность →</span>
      </div>

      <div
        ref={stageRef}
        className="relative inline-block max-w-full select-none overflow-hidden rounded-xl border border-stone-200 bg-stone-900 shadow-sm"
        onPointerDown={(e) => {
          if (e.button !== 0) return
          dragging.current = true
          setSplitFromClientX(e.clientX)
        }}
      >
        <img
          src={historicalUrl}
          alt="Исторический фасад (выпрямленный)"
          className="block max-h-[min(78vh,820px)] w-full object-contain"
          draggable={false}
        />
        <img
          src={modernUrl}
          alt="Современный фасад (выпрямленный)"
          className="pointer-events-none absolute inset-0 block max-h-[min(78vh,820px)] w-full object-contain"
          style={{ clipPath: `inset(0 0 0 ${split}%)` }}
          draggable={false}
        />
        <div
          className="pointer-events-none absolute inset-y-0 z-10 w-0.5 bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]"
          style={{ left: `${split}%`, transform: 'translateX(-50%)' }}
          aria-hidden
        />
        <div
          className="pointer-events-none absolute top-1/2 z-10 flex h-10 w-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-amber-400 bg-amber-50/95 text-amber-900 shadow-md"
          style={{ left: `${split}%` }}
          aria-hidden
        >
          ↔
        </div>
      </div>
    </div>
  )
}
