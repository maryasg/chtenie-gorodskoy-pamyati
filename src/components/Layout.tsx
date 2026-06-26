import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Карта' },
  { to: '/method', label: 'Метод' },
  { to: '/tour', label: 'Экскурсии' },
  { to: '/explorer', label: 'Исследователь' },
]

function FacadeLogo({ compact = false }: { compact?: boolean }) {
  return (
    <span
      className={`grid shrink-0 place-items-center rounded-full bg-arch-green-deep text-arch-surface shadow-sm ${
        compact ? 'h-8 w-8' : 'h-9 w-9 sm:h-10 sm:w-10'
      }`}
    >
      <svg
        viewBox="0 0 32 32"
        className={compact ? 'h-5 w-5' : 'h-5 w-5 sm:h-6 sm:w-6'}
        role="img"
        aria-label="Логотип: фасад с выделенным следом"
      >
        <rect x="7" y="5" width="18" height="22" rx="2" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M11 10h3M18 10h3M11 16h3M18 16h3M11 22h3M18 22h3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <rect x="17" y="15" width="5" height="5" rx="1" fill="var(--color-arch-gold)" />
      </svg>
    </span>
  )
}

function NavLinks({
  pathname,
  vertical = false,
  onNavigate,
}: {
  pathname: string
  vertical?: boolean
  onNavigate?: () => void
}) {
  return (
    <>
      {NAV.map(({ to, label }) => {
        const active = pathname === to || (to !== '/' && pathname.startsWith(to))
        return (
          <Link
            key={to}
            to={to}
            onClick={onNavigate}
            className={`block font-medium transition ${
              vertical
                ? `rounded-lg px-3 py-2.5 text-sm ${
                    active
                      ? 'bg-arch-green-deep text-arch-surface'
                      : 'text-arch-ink hover:bg-arch-surface-2'
                  }`
                : `rounded-full px-2 py-1.5 text-[11px] leading-none sm:px-3.5 sm:py-2 sm:text-sm ${
                    active
                      ? 'bg-arch-green-deep text-arch-surface'
                      : 'text-arch-muted hover:bg-arch-surface-2 hover:text-arch-ink'
                  }`
            }`}
          >
            {label}
          </Link>
        )
      })}
    </>
  )
}

export function Layout() {
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    setMenuOpen(false)
  }, [pathname])

  return (
    <div className="flex min-h-screen flex-col text-arch-ink">
      <header
        className="sticky top-2 z-20 mx-auto mt-2 w-[min(calc(100%-max(1rem,env(safe-area-inset-left)+env(safe-area-inset-right))),72rem)] rounded-full border border-arch-line bg-arch-surface/90 py-1.5 shadow-sm backdrop-blur-md sm:top-3 sm:mt-3 sm:py-2"
        style={{
          paddingLeft: 'max(0.5rem, env(safe-area-inset-left))',
          paddingRight: 'max(0.5rem, env(safe-area-inset-right))',
        }}
      >
        <div className="flex min-w-0 items-center justify-between gap-2 sm:gap-3">
          <Link to="/" className="inline-flex min-w-0 flex-1 items-center gap-1.5 hover:opacity-90 sm:gap-3 sm:flex-none">
            <FacadeLogo compact />
            <span className="min-w-0 leading-tight">
              <span className="block whitespace-nowrap text-[11px] font-semibold tracking-tight sm:text-base">
                Чтение городской памяти
              </span>
              <span className="hidden text-[10px] text-arch-muted sm:block sm:text-[11px]">
                MVP · 4 здания · Archiview
              </span>
            </span>
          </Link>

          <div
            className="relative shrink-0 sm:hidden"
            onMouseEnter={() => setMenuOpen(true)}
            onMouseLeave={() => setMenuOpen(false)}
          >
            <button
              type="button"
              aria-expanded={menuOpen}
              aria-controls="mobile-nav-menu"
              aria-label="Меню"
              onClick={() => setMenuOpen((open) => !open)}
              className="flex h-9 w-9 flex-col items-center justify-center gap-1 rounded-full text-arch-green-deep transition hover:bg-arch-surface-2"
            >
              <span className="block h-0.5 w-5 rounded-full bg-current" />
              <span className="block h-0.5 w-5 rounded-full bg-current" />
              <span className="block h-0.5 w-5 rounded-full bg-current" />
            </button>
            {menuOpen ? (
              <nav
                id="mobile-nav-menu"
                className="absolute right-0 top-[calc(100%+0.35rem)] z-30 min-w-[11.5rem] rounded-2xl border border-arch-line bg-arch-surface/95 p-1.5 shadow-lg backdrop-blur-md"
              >
                <NavLinks pathname={pathname} vertical onNavigate={() => setMenuOpen(false)} />
              </nav>
            ) : null}
          </div>

          <nav className="hidden shrink-0 gap-0.5 sm:flex sm:gap-1">
            <NavLinks pathname={pathname} />
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
