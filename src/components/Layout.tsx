import { Link, Outlet, useLocation } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Карта' },
  { to: '/tour', label: 'Экскурсия' },
  { to: '/explorer', label: 'Исследователь' },
]

export function Layout() {
  const { pathname } = useLocation()

  return (
    <div className="flex h-full min-h-screen flex-col bg-stone-50 text-stone-900">
      <header className="border-b border-stone-200 bg-white px-4 py-3 shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
          <div>
            <Link to="/" className="text-lg font-semibold text-stone-900 hover:text-stone-700">
              Чтение городской памяти через фасад
            </Link>
            <p className="text-xs text-stone-500">Пилот v1.0 · 4 здания · демо на пилотных данных</p>
          </div>
          <nav className="flex gap-1">
            {NAV.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                  pathname === to || (to !== '/' && pathname.startsWith(to))
                    ? 'bg-stone-900 text-white'
                    : 'text-stone-600 hover:bg-stone-100'
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-4">
        <Outlet />
      </main>
    </div>
  )
}
