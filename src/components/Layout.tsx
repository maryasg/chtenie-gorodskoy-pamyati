import { Link, Outlet, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Карта' },
  { to: '/tour', label: 'Экскурсия' },
  { to: '/explorer', label: 'Исследователь' },
]

export function Layout() {
  const { pathname } = useLocation()

  return (
    <div className="flex min-h-screen flex-col text-arch-ink">
      <header className="sticky top-3 z-20 mx-auto mt-3 w-[min(calc(100%-2rem),72rem)] rounded-full border border-arch-line bg-arch-surface/90 px-3 py-2 shadow-sm backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center gap-3 hover:opacity-90">
            <span
              className="grid h-10 w-10 place-items-center rounded-full bg-arch-green-deep text-[11px] font-bold tracking-tight text-arch-surface"
              aria-hidden
            >
              ПС
            </span>
            <span>
              <span className="block text-base font-semibold leading-tight tracking-tight">
                Чтение городской памяти
              </span>
              <span className="block text-[11px] text-arch-muted">Пилот · 4 здания · Archiview</span>
            </span>
          </Link>
          <nav className="flex gap-1">
            {NAV.map(({ to, label }) => {
              const active = pathname === to || (to !== '/' && pathname.startsWith(to))
              return (
                <Link
                  key={to}
                  to={to}
                  className={`rounded-full px-3.5 py-2 text-sm font-medium transition ${
                    active
                      ? 'bg-arch-green-deep text-arch-surface'
                      : 'text-arch-muted hover:bg-arch-surface-2 hover:text-arch-ink'
                  }`}
                >
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
