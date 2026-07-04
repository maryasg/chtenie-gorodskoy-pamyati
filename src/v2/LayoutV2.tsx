import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/v2', label: 'Главная', end: true },
  { to: '/v2/map', label: 'Карта' },
]

export function LayoutV2() {
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    setMenuOpen(false)
  }, [pathname])

  return (
    <div className="v2-root flex min-h-screen flex-col">
      <div className="border-b border-v2-line bg-v2-surface/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <Link to="/v2" className="min-w-0">
            <span className="v2-kicker block">Новый дизайн · preview</span>
            <span className="block truncate text-sm font-semibold tracking-tight sm:text-base">
              Чтение городской памяти
            </span>
          </Link>

          <nav className="hidden items-center gap-1 sm:flex">
            {NAV.map(({ to, label, end }) => {
              const active = end ? pathname === to : pathname.startsWith(to)
              return (
                <Link
                  key={to}
                  to={to}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                    active
                      ? 'bg-v2-accent text-white'
                      : 'text-v2-muted hover:bg-v2-surface-muted hover:text-v2-ink'
                  }`}
                >
                  {label}
                </Link>
              )
            })}
            <Link
              to="/"
              className="ml-2 rounded-full border border-v2-line px-3 py-1.5 text-sm text-v2-muted transition hover:text-v2-ink"
            >
              Текущий сайт
            </Link>
          </nav>

          <button
            type="button"
            aria-expanded={menuOpen}
            aria-label="Меню"
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded-lg border border-v2-line px-3 py-1.5 text-sm sm:hidden"
          >
            Меню
          </button>
        </div>

        {menuOpen ? (
          <nav className="border-t border-v2-line px-4 py-2 sm:hidden">
            <div className="flex flex-col gap-1">
              {NAV.map(({ to, label, end }) => {
                const active = end ? pathname === to : pathname.startsWith(to)
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`rounded-lg px-3 py-2 text-sm ${
                      active ? 'bg-v2-accent-soft text-v2-accent' : 'text-v2-ink'
                    }`}
                  >
                    {label}
                  </Link>
                )
              })}
              <Link to="/" className="rounded-lg px-3 py-2 text-sm text-v2-muted">
                Текущий сайт
              </Link>
            </div>
          </nav>
        ) : null}
      </div>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
