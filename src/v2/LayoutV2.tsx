import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/v2/map', label: 'Карта' },
  { to: '/v2#method', label: 'Метод' },
  { to: '/v2#objects', label: 'Объекты' },
]

export function LayoutV2() {
  const [menuOpen, setMenuOpen] = useState(false)
  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="v2-root flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-v2-line/80 bg-v2-bg/90 backdrop-blur-md">
        <div className="v2-container flex items-center justify-between gap-4 py-4">
          <Link to="/v2" className="min-w-0" onClick={closeMenu}>
            <span className="v2-mono-sm font-semibold text-v2-ink">Память стен</span>
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            {NAV.map(({ to, label }) => (
              <Link key={to} to={to} className="v2-mono-xs text-v2-muted transition hover:text-v2-ink">
                {label}
              </Link>
            ))}
            <Link to="/v2/map" className="v2-btn-dark">
              Карта
            </Link>
            <Link to="/" className="v2-mono-xs text-v2-muted hover:text-v2-ink">
              Текущий
            </Link>
          </nav>

          <button
            type="button"
            aria-expanded={menuOpen}
            aria-label="Меню"
            onClick={() => setMenuOpen((open) => !open)}
            className="border border-v2-line px-3 py-1.5 v2-mono-xs md:hidden"
          >
            Меню
          </button>
        </div>

        {menuOpen ? (
          <nav className="border-t border-v2-line px-4 py-3 md:hidden">
            <div className="flex flex-col gap-2">
              {NAV.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  onClick={closeMenu}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-v2-ink"
                >
                  {label}
                </Link>
              ))}
              <Link to="/v2/map" onClick={closeMenu} className="v2-btn-dark w-fit">
                Открыть карту
              </Link>
              <Link to="/" onClick={closeMenu} className="px-3 py-2 text-sm text-v2-muted">
                Текущий сайт
              </Link>
            </div>
          </nav>
        ) : null}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
