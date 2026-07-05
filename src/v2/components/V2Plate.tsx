import type { ReactNode } from 'react'
import { V2SquareMark } from './V2SquareMark'

export function V2Plate({
  code,
  title,
  description,
  meta,
  markColor,
  active = false,
  children,
}: {
  code?: string
  title: string
  description?: ReactNode
  meta?: string
  markColor?: string
  active?: boolean
  children?: ReactNode
}) {
  return (
    <article className="v2-plate-row">
      <div className="flex gap-3">
        <div className="pt-0.5">
          <V2SquareMark innerColor={markColor} active={active} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
            <h3 className="v2-mono-sm font-semibold text-v2-ink">{title}</h3>
            {code ? <span className="v2-mono-xs text-v2-muted">{code}</span> : null}
          </div>
          {description ? (
            <div className="mt-1.5 text-sm leading-relaxed text-v2-muted normal-case">{description}</div>
          ) : null}
          {meta ? <p className="v2-mono-xs mt-2 text-v2-muted">{meta}</p> : null}
          {children ? <div className="mt-3 normal-case">{children}</div> : null}
        </div>
      </div>
    </article>
  )
}

export function V2Manifest({
  kicker,
  title,
  count,
  children,
  className = '',
}: {
  kicker?: string
  title: string
  count?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`v2-panel ${className}`}>
      <header className="border-b border-v2-line px-4 py-4 sm:px-5">
        {kicker ? <p className="v2-kicker">{kicker}</p> : null}
        <div className="mt-1 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="v2-section-title normal-case">{title}</h2>
          {count ? <span className="v2-mono-xs text-v2-muted">{count}</span> : null}
        </div>
      </header>
      <div className="px-4 sm:px-5">{children}</div>
    </section>
  )
}
