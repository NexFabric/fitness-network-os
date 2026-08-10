import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearAuth, getTenantId } from '../api/client'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-full px-3.5 py-1.5 text-sm font-medium transition ${
    isActive
      ? 'bg-brand text-white shadow-sm'
      : 'text-slate-600 hover:bg-slate-100 hover:text-ink'
  }`

export default function Layout() {
  const navigate = useNavigate()
  const tenantId = getTenantId()

  function logout() {
    clearAuth()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-surface">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className="group flex items-center gap-2.5 focus-visible:outline-none"
            >
              <span
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-white shadow-sm transition group-hover:bg-brand-deep"
                aria-hidden="true"
              >
                G
              </span>
              <span className="text-base font-bold tracking-tight text-ink">
                GymClubNex
              </span>
            </Link>
            <nav className="flex flex-wrap gap-1" aria-label="Main">
              <NavLink to="/" end className={navClass}>
                Dashboard
              </NavLink>
              <NavLink to="/members" className={navClass}>
                Members
              </NavLink>
              <NavLink to="/locations" className={navClass}>
                Locations
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-2.5">
            {tenantId && (
              <span
                className="hidden items-center gap-1.5 rounded-full border border-slate-200 bg-surface px-2.5 py-1 font-mono text-xs text-slate-600 sm:inline-flex"
                title={tenantId}
              >
                <span
                  className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                  aria-hidden="true"
                />
                {tenantId.slice(0, 8)}…
              </span>
            )}
            <button type="button" onClick={logout} className="btn-secondary">
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
