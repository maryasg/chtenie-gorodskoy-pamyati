import type { ReactNode } from 'react'

export function V2Section({
  title,
  kicker,
  count,
  children,
  className = '',
}: {
  title: string
  kicker?: string
  count?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`v2-panel ${className}`}>
      <header className="border-b border-v2-line px-4 py-4 sm:px-5">
        {kicker ? <p className="v2-kicker">{kicker}</p> : null}
        <div className={`flex flex-wrap items-baseline justify-between gap-2 ${kicker ? 'mt-1' : ''}`}>
          <h2 className="v2-section-title">{title}</h2>
          {count ? <span className="v2-mono-xs text-v2-muted">{count}</span> : null}
        </div>
      </header>
      <div className="px-4 py-4 sm:px-5 normal-case">{children}</div>
    </section>
  )
}
