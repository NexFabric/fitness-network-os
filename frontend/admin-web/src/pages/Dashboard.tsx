import { Link } from 'react-router-dom'
import { getBaseUrl, getTenantId } from '../api/client'

export default function Dashboard() {
  const tenantId = getTenantId()
  const apiUrl = getBaseUrl()

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p className="mt-1 text-gray-600">
        Fitness Network OS — admin MVP shell.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Link
          to="/members"
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow"
        >
          <h2 className="font-semibold text-gray-900">Members</h2>
          <p className="mt-1 text-sm text-gray-600">
            List members for the current tenant.
          </p>
        </Link>
        <Link
          to="/locations"
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow"
        >
          <h2 className="font-semibold text-gray-900">Locations</h2>
          <p className="mt-1 text-sm text-gray-600">
            Branches / locations (Gym = Tenant, Branch = Location).
          </p>
        </Link>
      </div>

      <dl className="mt-8 space-y-2 rounded-lg border border-gray-200 bg-white p-5 text-sm">
        <div className="flex flex-wrap gap-2">
          <dt className="font-medium text-gray-700">API base</dt>
          <dd className="font-mono text-gray-900">{apiUrl}</dd>
        </div>
        <div className="flex flex-wrap gap-2">
          <dt className="font-medium text-gray-700">Tenant</dt>
          <dd className="font-mono text-gray-900">{tenantId ?? '—'}</dd>
        </div>
      </dl>
    </div>
  )
}
