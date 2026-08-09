import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearAuth, getTenantId } from '../api/client'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${
    isActive
      ? 'bg-indigo-600 text-white'
      : 'text-gray-700 hover:bg-gray-100'
  }`

export default function Layout() {
  const navigate = useNavigate()
  const tenantId = getTenantId()

  function logout() {
    clearAuth()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-lg font-semibold text-gray-900">
              GymClubNex Admin
            </Link>
            <nav className="flex flex-wrap gap-1">
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
          <div className="flex items-center gap-3 text-sm text-gray-600">
            {tenantId && (
              <span className="hidden font-mono text-xs sm:inline" title={tenantId}>
                Tenant: {tenantId.slice(0, 8)}…
              </span>
            )}
            <button
              type="button"
              onClick={logout}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-gray-700 hover:bg-gray-50"
            >
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
