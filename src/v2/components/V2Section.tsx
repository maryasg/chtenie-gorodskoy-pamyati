import type { ReactNode } from 'react'

export function V2Section({
  title,
  kicker,
  children,
  className = '',
}: {
  title: string
  kicker?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`v2-card p-5 sm:p-6 ${className}`}>
      {kicker ? <p className="v2-kicker">{kicker}</p> : null}
      <h2 className={`v2-section-title ${kicker ? 'mt-1' : ''}`}>{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  )
}
