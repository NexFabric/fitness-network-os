import { useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'

type Location = {
  id: string
  name: string
  timezone: string
  address: string | null
}

export default function Locations() {
  const [locations, setLocations] = useState<Location[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await api<Location[]>('/api/v1/locations')
        if (!cancelled) setLocations(data)
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof ApiError
              ? `${e.status}: ${e.message}`
              : e instanceof Error
                ? e.message
                : 'Failed to load locations',
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Locations</h1>
      <p className="mt-1 text-sm text-gray-600">
        GET /api/v1/locations — Branch = Location (requires locations:read)
      </p>

      {loading && (
        <p className="mt-6 text-gray-500" role="status">
          Loading…
        </p>
      )}

      {error && (
        <div
          className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="mt-6 overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-700">Name</th>
                <th className="px-4 py-3 font-medium text-gray-700">Timezone</th>
                <th className="px-4 py-3 font-medium text-gray-700">Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {locations.length === 0 ? (
                <tr>
                  <td
                    colSpan={3}
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    No locations found.
                  </td>
                </tr>
              ) : (
                locations.map((loc) => (
                  <tr key={loc.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {loc.name}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">
                      {loc.timezone}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {loc.address ?? '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
